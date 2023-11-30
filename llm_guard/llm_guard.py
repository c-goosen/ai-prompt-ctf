import decimal
from fastapi import Request

from app_config import settings
from httpx import HTTPStatusError
from tenacity import retry, stop_after_attempt, retry_if_exception_type


class LLMGaurdV1:
    API_URL = settings.HUGGINGFACE_INFERENCE_API_URL
    headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

    def __init__(self):
        self.API_URL = settings.HUGGINGFACE_INFERENCE_API_URL
        self.headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

    @retry(retry=retry_if_exception_type(HTTPStatusError), stop=stop_after_attempt(5))
    async def query(self, request: Request, prompt: str):
        json_payload = {
            "inputs": prompt,
            "options": {"wait_for_model": True, "use_cache": True},
        }
        # s = requests.Session()
        # retries = Retry(total=5, backoff_factor=15, status_forcelist=[503])
        # s.mount("https://", HTTPAdapter(max_retries=retries))
        response = await request.app.requests_client.post(
            url=str(LLMGaurdV1.API_URL), json=json_payload, headers=LLMGaurdV1.headers
        )
        response.raise_for_status()
        # resp_data = response.json()

        resp_json = response.json(parse_float=decimal.Decimal)
        try:
            print(resp_json[0])
            print("No Exception")
        except Exception as e:
            print("Exception")
            # time.sleep(5)
            # response = s.post(
            #     LLMGaurdV1.API_URL, headers=LLMGaurdV1.headers, json=json_payload
            # )
            # resp_json = response.json(parse_float=decimal.Decimal)

        print(response.status_code)
        print(resp_json)

        return resp_json
