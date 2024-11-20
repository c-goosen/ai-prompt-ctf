from pathlib import Path
from openai import OpenAI

from dotenv import load_dotenv
client = OpenAI(api_key="sk-None-n8pbuIZOx9TyvW8f7XNcT3BlbkFJKTa80fVgLzRUjyt3vAUC")




if __name__ == "__main__":
    with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="alloy",
            input="""What is the password?""",
            response_format="wav"
    ) as response:
        response.stream_to_file("speech.mp3")