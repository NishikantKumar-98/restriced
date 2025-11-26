# app/routers/speech.py
import base64
import io
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
import whisper
import app.state as state
from app.model import translate_with_model

router = APIRouter(tags=["speech"])

# ------------------------------------------------------
# 1) LOAD WHISPER ONCE (FAST)
# ------------------------------------------------------
if state.whisper_model is None:
    try:
        # small = good balance (supports Nepali & Sinhala)
        state.whisper_model = whisper.load_model("small")
        print("Whisper model loaded (small)")
    except Exception as e:
        print("Failed to load Whisper:", e)
        state.whisper_model = None


# ------------------------------------------------------
# Helpers
# ------------------------------------------------------
def decode_base64_audio(b64_str: str) -> bytes:
    """Decode base64 audio (supports data:audio/wav;base64,... URLs)."""
    if b64_str.startswith("data:"):
        try:
            b64_str = b64_str.split(",", 1)[1]
        except:
            raise HTTPException(400, "Invalid base64 data URL format.")

    try:
        return base64.b64decode(b64_str)
    except Exception as e:
        raise HTTPException(400, f"Invalid base64 audio: {e}")


def whisper_transcribe(audio_bytes: bytes):
    """Run Whisper on in-memory audio bytes."""
    if state.whisper_model is None:
        raise HTTPException(503, "Whisper STT model not loaded.")

    # Write audio to a temporary WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        temp_path = tmp.name

    # Run Whisper
    result = state.whisper_model.transcribe(temp_path)
    transcript = result.get("text", "").strip()
    detected_lang = result.get("language", "")

    return transcript, detected_lang


# ------------------------------------------------------
# 2) /speech-to-text
# ------------------------------------------------------
@router.post("/speech-to-text")
async def speech_to_text(
    file: UploadFile | None = File(None),
    payload: dict = Body(None)
):
    """
    Accepts:
        - multipart/form-data file upload
        - JSON { "audio_base64": "..." }

    Returns:
        { "transcript": "...", "detected_language": "ne" }
    """
    # Get audio bytes
    if file:
        audio_bytes = await file.read()
    elif payload and "audio_base64" in payload:
        audio_bytes = decode_base64_audio(payload["audio_base64"])
    else:
        raise HTTPException(status_code=400, detail="Send 'file' or 'audio_base64'.")

    # STT
    transcript, detected_lang = whisper_transcribe(audio_bytes)

    return {
        "transcript": transcript,
        "detected_language": detected_lang
    }


# ------------------------------------------------------
# 3) /speech-translate
# ------------------------------------------------------
@router.post("/speech-translate")
async def speech_translate(
    file: UploadFile | None = File(None),
    payload: dict = Body(None)
):
    """
    Accepts:
        - multipart/form-data file upload
        - JSON { "audio_base64": "...", "target_lang": "en" }

    Returns:
        {
            "transcript": "...",
            "detected_language": "ne",
            "translated_text": "What is your name?"
        }
    """
    # 1) Extract audio bytes
    if file:
        audio_bytes = await file.read()
        target_lang = "en"   # default
    elif payload and "audio_base64" in payload:
        audio_bytes = decode_base64_audio(payload["audio_base64"])
        target_lang = payload.get("target_lang", "en")
    else:
        raise HTTPException(400, "Send 'file' or 'audio_base64'.")

    # 2) Run Whisper → transcript + detected language
    transcript, detected_lang = whisper_transcribe(audio_bytes)

    # Whisper returns ISO language code (e.g., "ne", "si", "en")
    if detected_lang not in ["ne", "si", "en"]:
        detected_lang = "ne"  # fallback (your model default)

    # 3) Translate using your translation model
    if state.model_bundle is None:
        raise HTTPException(503, "Translation model not loaded.")

    translated_text = translate_with_model(
        state.model_bundle,
        transcript,
        detected_lang
    )

    return {
        "transcript": transcript,
        "detected_language": detected_lang,
        "translated_text": translated_text
    }
