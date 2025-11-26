from typing import Optional

# Shared state for the FastAPI app
model_bundle: Optional[dict] = None
whisper_model = None  # Add this line for speech router

# Note: No longer storing ocr_reader since we use pytesseract directly
