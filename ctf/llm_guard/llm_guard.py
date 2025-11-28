from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline


class LLMGuardLocalBase:
    def __init__(
        self,
    ):
        self.MODEL = "protectai/deberta-v3-base-prompt-injection-v2"
        self.TOKENIZER = "protectai/deberta-v3-base-prompt-injection-v2"
        self.max_length = 512
        self.revision = "main"
        self.device = "cpu"

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
            max_length=self.max_length,
            # device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
            revision=self.revision,
            device=self.device,
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
        super().__init__()
        # self.MODEL = "meta-llama/Prompt-Guard-86M"
        self.MODEL = "protectai/deberta-v3-base-prompt-injection-v2"
        # self.TOKENIZER = "meta-llama/Prompt-Guard-86M"
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
