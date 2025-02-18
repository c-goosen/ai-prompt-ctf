# import random
# from hashlib import sha256

# from app_config import settings
from transformers import AutoModel, AutoProcessor
import torch

import torch
from transformers import Speech2TextProcessor, Speech2TextForConditionalGeneration

def audio_to_text(audio_file):
    model = Speech2TextForConditionalGeneration.from_pretrained("facebook/s2t-medium-mustc-multilingual-st")
    processor = Speech2TextProcessor.from_pretrained("facebook/s2t-medium-mustc-multilingual-st")
    inputs = processor(audio_file, return_tensors="pt")
    generated_ids = model.generate(
        inputs["input_features"],
        attention_mask=inputs["attention_mask"],
        forced_bos_token_id=processor.tokenizer.lang_code_to_id["fr"],
    )

    translation = processor.batch_decode(generated_ids, skip_special_tokens=True)
    print(f"audio_to_text --> Translation {translation}")
    return translation


def image_to_text(image_file, prompt: str):

    model = AutoModel.from_pretrained("unum-cloud/uform-gen2-qwen-500m", trust_remote_code=True)
    processor = AutoProcessor.from_pretrained("unum-cloud/uform-gen2-qwen-500m", trust_remote_code=True)

    inputs = processor(text=[prompt], images=[image_file], return_tensors="pt")
    with torch.inference_mode():
         output = model.generate(
            **inputs,
            do_sample=False,
            use_cache=True,
            max_new_tokens=256,
            eos_token_id=151645,
            pad_token_id=processor.tokenizer.pad_token_id
        )

    prompt_len = inputs["input_ids"].shape[1]
    decoded_text = processor.batch_decode(output[:, prompt_len:])[0]
    print(f"image_to_text --> Translation {decoded_text}")

    return decoded_text
