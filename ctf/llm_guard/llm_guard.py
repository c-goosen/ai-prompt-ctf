from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline


class LLMGuardLocalBase:
    def __init__(
        self,
    ):
        self.MODEL = "protectai/deberta-v3-base-prompt-injection-v2"
        self.TOKENIZER = "protectai/deberta-v3-base-prompt-injection-v2"

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
            # device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
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
        # self.MODEL = "meta-llama/Prompt-Guard-86M"
        self.MODEL = "protectai/deberta-v3-base-prompt-injection-v2"
        # self.TOKENIZER = "meta-llama/Prompt-Guard-86M"
        self.TOKENIZER = "protectai/deberta-v3-base-prompt-injection-v2"


class PromptGuardGoose(LLMGuardLocalBase):
    def __init__(
        self,
    ):
        self.MODEL = "cgoosen/prompt-tackler"
        self.TOKENIZER = "cgoosen/prompt-tackler"
