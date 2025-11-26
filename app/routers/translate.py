from fastapi import APIRouter, HTTPException
import traceback
import app.state as state
from app.schemas import TranslateRequest, TranslateResponse
from app.model import translate_with_model

router = APIRouter()

@router.post("/translate-text", response_model=TranslateResponse)
async def translate_text(payload: TranslateRequest):
    if state.model_bundle is None:
        raise HTTPException(status_code=503, detail="Model not loaded.")

    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text")

    try:
        translated = translate_with_model(state.model_bundle, text, payload.source_lang)
        return TranslateResponse(translated_text=translated)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Translation error: {e}")