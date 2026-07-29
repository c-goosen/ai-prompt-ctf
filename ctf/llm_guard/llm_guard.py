import asyncio

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline

# Cache loaded pipelines so the model/tokenizer are only loaded from disk once
# per configuration, instead of on every query (which was slow and churned
# memory for the guard checks run on each message).
_PIPELINE_CACHE: dict = {}


class LLMGuardLocalBase:
    def __init__(
        self,
    ):
        self.MODEL = "protectai/deberta-v3-base-prompt-injection-v2"
        self.TOKENIZER = "protectai/deberta-v3-base-prompt-injection-v2"
        self.max_length = 512
        self.revision = "main"
        self.device = "cpu"

    def _get_pipeline(self):
        key = (
            self.MODEL,
            self.TOKENIZER,
            self.revision,
            self.max_length,
            self.device,
        )
        nlp = _PIPELINE_CACHE.get(key)
        if nlp is None:
            print(f"Loading model --> {self.MODEL} on {self.device}")
            tokenizer = AutoTokenizer.from_pretrained(self.TOKENIZER)
            model = AutoModelForSequenceClassification.from_pretrained(
                self.MODEL
            )
            nlp = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                truncation=True,
                max_length=self.max_length,
                revision=self.revision,
                device=self.device,
            )
            _PIPELINE_CACHE[key] = nlp
        return nlp

    def _classify(self, prompt: str) -> list:
        nlp = self._get_pipeline()

        classification_results = nlp(prompt)
        if isinstance(classification_results, list):
            classification_results = classification_results[0]
        return classification_results

    async def query(self, prompt: str) -> list:
        """
        Locally run and prompt a AutoModelForSequenceClassification LLM.

        Runs in a worker thread since both model loading (first call) and
        inference are blocking, CPU-bound work that would otherwise stall
        the event loop for every other concurrent request.
        :param prompt:
        :return:
        """
        return await asyncio.to_thread(self._classify, prompt)


class PromptGuardMeta(LLMGuardLocalBase):
    def __init__(
        self,
    ):
        super().__init__()
        self.MODEL = "protectai/deberta-v3-base-prompt-injection-v2"
        self.TOKENIZER = "protectai/deberta-v3-base-prompt-injection-v2"
        self.revision = "main"
        self.device = "cpu"


class PromptGuardGoose(LLMGuardLocalBase):
    def __init__(
        self,
    ):
        self.MODEL = "cgoosen/prompt-tackler"
        self.TOKENIZER = "cgoosen/prompt-tackler"
        self.max_length = 512
        self.revision = "main"
        self.device = "cpu"


class PromptGuardGooseModernBERT(LLMGuardLocalBase):
    def __init__(
        self,
    ):
        self.MODEL = "cgoosen/prompt-tackler_modernbert"
        self.TOKENIZER = "cgoosen/prompt-tackler_modernbert"
        self.max_length = 8000
        self.revision = "1751267f4aa5caa81bee391312c094acac98ca43"
        self.device = "cpu"
