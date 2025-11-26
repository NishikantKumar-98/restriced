# app/routers/ocr.py
from fastapi import APIRouter, HTTPException
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import base64
import io
import os
from app.schemas import OCRRequest, OCRResponse
import app.state as state

router = APIRouter(tags=["ocr"])

# Configure Tesseract path
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Check Tesseract availability
TESSERACT_AVAILABLE = True
try:
    _ = pytesseract.get_tesseract_version()
except Exception:
    TESSERACT_AVAILABLE = False

def preprocess_image(image: Image.Image) -> Image.Image:
    """Preprocess image for better OCR results"""
    # Convert to grayscale for better OCR
    if image.mode != 'L':
        image = image.convert('L')
    
    # Enhance contrast moderately (1.5x instead of 2.0x)
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    
    # Enhance sharpness moderately
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.5)
    
    # Apply slight denoise only if needed
    # image = image.filter(ImageFilter.MedianFilter(size=3))
    
    return image

def detect_script(image: Image.Image):
    """Detect script using Tesseract OSD"""
    try:
        osd_data = pytesseract.image_to_osd(image)
        for line in osd_data.split("\n"):
            if "Script" in line:
                return line.split(":")[1].strip()
    except Exception:
        return "Latin"
    return "Latin"

SCRIPT_MAP = {
    "Devanagari": "nep",
    "Sinhala": "sin", 
    "Latin": "eng",
}

# Map source_lang to Tesseract language codes
SOURCE_LANG_TO_TESS = {
    "ne": "nep",
    "si": "sin",
    "en": "eng",
}

# Reverse map for script detection
TESS_TO_SCRIPT = {
    "nep": "Devanagari",
    "sin": "Sinhala",
    "eng": "Latin",
}

@router.post("/ocr-translate", response_model=OCRResponse)
async def ocr_process(request: OCRRequest):
    """
    OCR endpoint that processes base64 image and returns extracted text with optional translation
    """
    
    if not TESSERACT_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Tesseract not installed. Please install Tesseract OCR."
        )

    # Validate input
    if not request.image_base64:
        raise HTTPException(status_code=400, detail="image_base64 is required")
    
    try:
        # Handle data URL format and strip whitespace
        b64_data = request.image_base64.strip()
        if b64_data.startswith("data:"):
            b64_data = b64_data.split(",", 1)[1]
        
        # Decode base64
        img_bytes = base64.b64decode(b64_data, validate=True)
        if len(img_bytes) == 0:
            raise HTTPException(status_code=400, detail="Decoded image is empty")
            
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        
        # Ensure minimum size for OCR (Tesseract works better with larger images)
        width, height = image.size
        if width < 300 or height < 300:
            # Scale up if too small (maintain aspect ratio)
            scale = max(300 / width, 300 / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create a copy for script detection (keep original)
        script_detection_image = image.copy()
        
        # Preprocess image for OCR (grayscale, contrast, sharpness)
        processed_image = preprocess_image(image.copy())
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")

    # Determine OCR language - use source_lang if provided, otherwise detect
    forced_lang = None
    if request.source_lang and request.source_lang in SOURCE_LANG_TO_TESS:
        forced_lang = SOURCE_LANG_TO_TESS[request.source_lang]
        script = TESS_TO_SCRIPT.get(forced_lang, "Unknown")
    else:
        # Detect script automatically using original image
        script = detect_script(script_detection_image)
        forced_lang = SCRIPT_MAP.get(script, "eng")

    # Perform OCR with fallback strategy
    text = ""
    detected_lang = forced_lang if forced_lang else "eng"
    languages_to_try = []
    
    if forced_lang:
        languages_to_try.append(forced_lang)
    
    # Add fallback languages
    if forced_lang != "eng":
        languages_to_try.append("eng")
    if forced_lang not in ["nep", "eng"]:
        languages_to_try.append("nep")
    if forced_lang not in ["sin", "eng"]:
        languages_to_try.append("sin")
    
    # Remove duplicates while preserving order
    languages_to_try = list(dict.fromkeys(languages_to_try))
    
    # Try different PSM modes for better text extraction
    # PSM modes: 3 (fully automatic), 6 (uniform block), 7 (single text line), 11 (sparse text), 12 (text with OSD)
    psm_modes = ['6', '3', '7', '11']
    
    # Try OCR with multiple languages and PSM modes
    for lang in languages_to_try:
        for psm in psm_modes:
            try:
                ocr_config = f'--oem 3 --psm {psm}'
                text = pytesseract.image_to_string(processed_image, lang=lang, config=ocr_config).strip()
                if text and len(text) > 0:
                    # Update script and lang based on successful extraction
                    detected_lang = lang
                    script = TESS_TO_SCRIPT.get(lang, script)
                    break
            except Exception as e:
                print(f"OCR failed for language {lang} with PSM {psm}: {e}")
                continue
        
        if text:
            break
    
    # If still no text, try with original image (not preprocessed)
    if not text:
        for lang in languages_to_try:
            for psm in ['6', '3']:
                try:
                    ocr_config = f'--oem 3 --psm {psm}'
                    text = pytesseract.image_to_string(image, lang=lang, config=ocr_config).strip()
                    if text and len(text) > 0:
                        detected_lang = lang
                        script = TESS_TO_SCRIPT.get(lang, script)
                        break
                except Exception as e:
                    continue
            if text:
                break
    
    # Last resort - try with no language specified (defaults to English)
    if not text:
        try:
            text = pytesseract.image_to_string(processed_image, config='--oem 3 --psm 6').strip()
            if not text:
                text = pytesseract.image_to_string(processed_image, config='--oem 3 --psm 3').strip()
            if text:
                detected_lang = "eng"
                script = "Latin"
        except Exception as e:
            # Final fallback
            try:
                text = pytesseract.image_to_string(processed_image).strip()
                if text:
                    detected_lang = "eng"
                    script = "Latin"
            except Exception as e2:
                pass  # Will return empty text if all fails

    # Optional translation
    translated_text = None
    
    if state.model_bundle and text:
        try:
            from app.model import translate_with_model
            source_map = {"nep": "ne", "sin": "si", "eng": "en"}
            source_lang = source_map.get(detected_lang, request.source_lang or "ne")
            translated_text = translate_with_model(state.model_bundle, text, source_lang)
        except Exception as e:
            print(f"Translation failed: {e}")

    return OCRResponse(
        detected_script=script,
        detected_language=detected_lang,
        extracted_text=text,
        translated_text=translated_text
    )
