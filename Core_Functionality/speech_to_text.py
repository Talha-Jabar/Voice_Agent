from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

def transcribe_audio(audio_file_path: str, api_key: str | None) -> str:
    client = OpenAI(api_key=api_key)
    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

