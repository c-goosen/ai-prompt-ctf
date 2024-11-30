from transformers import AutoTokenizer, AutoModelForSequenceClassification


def download_models():
    models = ['protectai/deberta-v3-base-prompt-injection-v2', 'cgoosen/prompt-tackler']
    for m in models:
        _ = AutoTokenizer.from_pretrained(m)
        _ = AutoModelForSequenceClassification.from_pretrained(m)