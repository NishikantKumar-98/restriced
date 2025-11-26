# Paste into app/model.py (replace previous helpers / translate function)
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from typing import Dict, Any
import traceback

# config (keep your MODEL_NAME and generation settings)
MODEL_NAME = "facebook/nllb-200-distilled-600M"
MAX_GEN_LENGTH = 128
NUM_BEAMS = 4
EARLY_STOPPING = True

def load_model(path: str = None) -> Dict[str, Any]:
    print(f"Loading tokenizer and model: {MODEL_NAME}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
        print("Fast tokenizer loaded.")
    except Exception:
        print("Fast tokenizer failed, falling back to slow. Traceback:")
        traceback.print_exc()
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False)
        print("Slow tokenizer loaded.")
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME, low_cpu_mem_usage=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        try:
            model = model.to(device)
            print("Moved model to CUDA")
        except Exception:
            print("Could not move model to CUDA; continuing on CPU")
            device = "cpu"
    return {"tokenizer": tokenizer, "model": model, "device": device, "name": MODEL_NAME}

def _get_lang_id_safe(tokenizer, lang_code: str):
    """
    Try many variants to find the int id in the tokenizer vocab / mappings.
    Returns int id or None.
    """
    # 1) direct mapping (preferred)
    if hasattr(tokenizer, "lang_code_to_id") and lang_code in tokenizer.lang_code_to_id:
        return tokenizer.lang_code_to_id[lang_code]

    vocab = tokenizer.get_vocab()

    # 2) try common token forms used by NLLB: "<eng_Latn>" and "<2eng_Latn>"
    candidates = [
        f"<{lang_code}>",
        f"<2{lang_code}>",
        f"▁<{lang_code}>",
        f"▁{lang_code}",
        lang_code
    ]

    for cand in candidates:
        if cand in vocab:
            return vocab[cand]

    # 3) fallback: try converting token string to id if tokenizer supports it
    try:
        for cand in candidates:
            try:
                tid = tokenizer.convert_tokens_to_ids(cand)
                if isinstance(tid, int) and tid != tokenizer.unk_token_id:
                    return tid
            except Exception:
                continue
    except Exception:
        pass

    return None

def translate_with_model(bundle: Dict[str, Any], text: str, source_lang: str) -> str:
    tokenizer = bundle["tokenizer"]
    model = bundle["model"]
    device = bundle.get("device", "cpu")

    # friendly -> NLLB codes (ensure correct values)
    lang_map = {
        "ne": "npi_Deva",
        "si": "sin_Sinh",
        "en": "eng_Latn"
    }
    src = lang_map.get(source_lang, "npi_Deva")
    tgt = "eng_Latn"

    # Set source/tgt on tokenizer when supported
    try:
        tokenizer.src_lang = src
    except Exception:
        pass
    try:
        # some tokenizers support src/tgt attributes
        tokenizer.tgt_lang = tgt
    except Exception:
        pass

    # Tokenize input
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)

    # move tensors to device
    if device == "cuda":
        inputs = {k: v.to("cuda") for k, v in inputs.items()}

    # Resolve target language id safely
    lang_id = _get_lang_id_safe(tokenizer, tgt)

    gen_kwargs = {
        "max_length": MAX_GEN_LENGTH,
        "num_beams": NUM_BEAMS,
        "early_stopping": EARLY_STOPPING,
    }

    if lang_id is not None:
        # Use forced BOS token for target language
        outputs = model.generate(
            **inputs,
            forced_bos_token_id=lang_id,
            **gen_kwargs
        )
    else:
        # Log fallback (you can print or logger)
        print(f"[WARN] Could not find lang-id for target {tgt}; generating without forced_bos.")
        outputs = model.generate(**inputs, **gen_kwargs)

    translated = tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
    return translated
