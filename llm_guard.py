import json
import requests
from app_config import settings


class LLMGaurdV1:
    API_URL = "https://api-inference.huggingface.co/models/cgoosen/llm_firewall_distilbert-base-uncased"
    headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

    def __init__(self):
        self.API_URL = "https://api-inference.huggingface.co/models/cgoosen/llm_firewall_distilbert-base-uncased"
        self. headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

    def query(self, payload):
        response = requests.post(LLMGaurdV1.API_URL, headers=LLMGaurdV1.headers, json=payload)
        return response.json()
