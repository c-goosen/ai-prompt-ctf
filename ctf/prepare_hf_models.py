from transformers import AutoTokenizer, AutoModelForSequenceClassification

import os
os.environ['CURL_CA_BUNDLE'] = ''

def download_models():
    models = [
        "protectai/deberta-v3-base-prompt-injection-v2",
        "cgoosen/prompt-tackler",
        # "facebook/s2t-medium-mustc-multilingual-st",
        # "unum-cloud/uform-gen2-qwen-500m"
    ]
    for m in models:
        _ = AutoTokenizer.from_pretrained(m)
        _ = AutoModelForSequenceClassification.from_pretrained(m)
