import os
from elevenlabs import ElevenLabs, play
from dotenv import load_dotenv
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
ELEVENLABS_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"

def generate_speech(text: str, voice_id: str = "JBFqnCBsd6RMkjVDRZzb"):
    
    audio = client.text_to_speech.convert(
        text=text,
        output_format="mp3_44100_128", 
        voice_id=voice_id, 
        model_id="eleven_multilingual_v2"
    )
    play(audio)

