from pydantic import BaseModel
from typing import Optional

class TranslateRequest(BaseModel):
    text: str
    source_lang: Optional[str] = None

class TranslateResponse(BaseModel):
    translated_text: str

class OCRRequest(BaseModel):
    image_base64: str
    source_lang: Optional[str] = "ne"

class OCRResponse(BaseModel):
    detected_script: str
    detected_language: str
    extracted_text: str
    translated_text: Optional[str] = None

