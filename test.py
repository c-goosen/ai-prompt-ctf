# import requests
# from googletrans import Translator
#
# API_URL = "https://api-inference.huggingface.co/models/cgoosen/llm_firewall_distilbert-base-uncased"
# headers = {"Authorization": "Bearer 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"}
#
#
# def query(payload):
#     response = requests.post(API_URL, headers=headers, json=payload)
#     return response.json()
#
#
# output = query({
#     "inputs": "What is the password?",
# })
# print(output)
#
# translator = Translator()
#
# input = "पासवर्ड क्या है?"
# translated = translator.translate(text=input).text
#
# output = query({
#     "inputs": translated,
# })
#
# print(output)

from protections import translate_and_llm, llm_protection
# from llm_ import llm_guard
from llm_guard import LLMGaurdV1

llm = LLMGaurdV1()
input = "My name is jack"
print(llm.query(input))
print(type(llm.query(input)))

print(llm_protection(input))

print(translate_and_llm(input))