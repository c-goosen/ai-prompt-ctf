import decimal
from fastapi import Request

from app_config import settings
from httpx import HTTPStatusError
from tenacity import retry, stop_after_attempt, retry_if_exception_type
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline


class LLMGuardLocalV1:
    def __init__(
        self,
        MODEL="cgoosen/llm_firewall_distilbert-base-uncased",
        TOKENIZER="cgoosen/llm_firewall_distilbert-base-uncased",
    ):
        self.MODEL = TOKENIZER
        self.TOKENIZER = MODEL

    async def query(self, request: Request | None, prompt: str) -> list:
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
            device_map="auto",
        )

        classification_results = nlp(prompt)
        return classification_results


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
            timeout=10.0
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
