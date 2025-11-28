import os

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from ctf.llm_guard.llm_guard import (
    PromptGuardMeta,
    PromptGuardGoose,
    PromptGuardGooseModernBERT,
)

os.environ["CURL_CA_BUNDLE"] = ""


def download_models():
    models = [
        PromptGuardMeta(),
        PromptGuardGoose(),
        PromptGuardGooseModernBERT(),
        # "facebook/s2t-medium-mustc-multilingual-st",
        # "unum-cloud/uform-gen2-qwen-500m"
    ]
    for m in models:
        AutoTokenizer.from_pretrained(
            pretrained_model_name_or_path=m.TOKENIZER,
            revision=getattr(m, "revision", None),
        )
        AutoModelForSequenceClassification.from_pretrained(
            pretrained_model_name_or_path=m.MODEL,
            revision=getattr(m, "revision", None),
        )
