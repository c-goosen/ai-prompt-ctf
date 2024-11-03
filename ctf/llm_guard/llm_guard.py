import decimal

import torch
from fastapi import Request
from httpx import HTTPStatusError
from tenacity import retry, stop_after_attempt, retry_if_exception_type
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline

from ctf.app_config import settings


class LLMGuardLocalBase:
    def __init__(
        self,
    ):
        self.MODEL = "cgoosen/llm_firewall_distilbert-base-uncased"
        self.TOKENIZER = "cgoosen/llm_firewall_distilbert-base-uncased"

    async def query(self, prompt: str) -> list:
        """
        Locally run and prompt a AutoModelForSequenceClassification LLM.
        :param prompt:
        :return:
        """
        tokenizer = AutoTokenizer.from_pretrained(self.TOKENIZER)
        model = AutoModelForSequenceClassification.from_pretrained(self.MODEL)
        nlp = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            truncation=True,
            max_length=1024,
            #device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
            device="cpu",
        )
        print(f"Running model --> {self.MODEL} on cpu")

        classification_results = nlp(prompt)
        if isinstance(classification_results, list):
            classification_results = classification_results[0]
        return classification_results
    
class PromptGuardMeta(LLMGuardLocalBase):
    def __init__(
        self,
    ):
        #self.MODEL = "meta-llama/Prompt-Guard-86M"
        self.MODEL = "protectai/deberta-v3-base-prompt-injection-v2"
        #self.TOKENIZER = "meta-llama/Prompt-Guard-86M"
        self.TOKENIZER = "protectai/deberta-v3-base-prompt-injection-v2"

class PromptGuardGoose(LLMGuardLocalBase):
    def __init__(
        self,
    ):
        self.MODEL = "cgoosen/prompt-tackler"
        self.TOKENIZER = "cgoosen/prompt-tackler"

class LLMGuardV1:
    API_URL = settings.HUGGINGFACE_INFERENCE_API_URL
    headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

    def __init__(self):
        self.API_URL = settings.HUGGINGFACE_INFERENCE_API_URL
        self.headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"
        }

    @retry(
        retry=retry_if_exception_type(HTTPStatusError),
        stop=stop_after_attempt(5),
    )
    async def query(self, request: Request, prompt: str):
        json_payload = {
            "inputs": prompt,
            "options": {"wait_for_model": True, "use_cache": True},
        }
        response = await request.app.requests_client.post(
            url=str(LLMGuardV1.API_URL),
            json=json_payload,
            headers=LLMGuardV1.headers,
            timeout=10.0,
        )
        response.raise_for_status()

        resp_json = response.json(parse_float=decimal.Decimal)
        try:
            print(resp_json[0])
            print("No Exception")
        except Exception as e:
            print(f"Exception -> {e}")

        print(response.status_code)
        print(resp_json)

        return resp_json
