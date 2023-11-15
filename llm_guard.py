import decimal
import json
import requests
from app_config import settings
from requests.adapters import HTTPAdapter, Retry

class LLMGaurdV1:
    API_URL = "https://api-inference.huggingface.co/models/cgoosen/llm_firewall_distilbert-base-uncased"
    headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

    def __init__(self):
        self.API_URL = "https://api-inference.huggingface.co/models/cgoosen/llm_firewall_distilbert-base-uncased"
        self.headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

    def query(self, prompt):
        json_payload = {"inputs": prompt, "wait_for_model": True, "use_cache": True}
        s = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        s.mount('https://', HTTPAdapter(max_retries=retries))

        response = s.post(
            LLMGaurdV1.API_URL, headers=LLMGaurdV1.headers, json=json_payload
        )
        resp_json = response.json(parse_float=decimal.Decimal)
        print(resp_json)
        return resp_json
