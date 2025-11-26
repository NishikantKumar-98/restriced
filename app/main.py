# app/main.py
"""
FastAPI app with:
- /translate-text  -> text translation (routers/translate.py)
- /ocr-translate    -> image/pdf OCR (routers/ocr.py)

Uses Tesseract OCR + PyMuPDF (pymupdf). Make sure these are installed in your venv:
    pip install fastapi "uvicorn[standard]" pytesseract pymupdf pillow transformers torch sentencepiece tokenizers huggingface-hub protobuf
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import traceback, sys

# Use shared state module
import app.state as state

# Import model loader
from app.model import load_model

# Include routers (make sure routers/__init__.py exists)
from app.routers.translate import router as translate_router
from app.routers.ocr import router as ocr_router
from app.routers.speech import router as speech_router

app = FastAPI(title="NLLB Translation + OCR (Tesseract + PyMuPDF)")

# CORS - allow all origins during development; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers (optionally add prefixes or tags)
app.include_router(translate_router)  # routes from routers/translate.py
app.include_router(ocr_router)        # routes from routers/ocr.py
# app.include_router(speech_router)

@app.on_event("startup")
async def startup_event():
    # Load translation model into shared state
    try:
        state.model_bundle = load_model()
        model_name = state.model_bundle.get("name") if state.model_bundle else None
        print("Translation model loaded:", model_name)
    except Exception:
        state.model_bundle = None
        print("Failed to load translation model:", file=sys.stderr)
        traceback.print_exc()

    # Check Tesseract availability
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print("Tesseract version:", version)
    except Exception:
        print("Tesseract not available - OCR features will be limited:", file=sys.stderr)
        traceback.print_exc()
