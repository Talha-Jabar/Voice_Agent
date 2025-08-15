
import gradio as gr
import os
from dotenv import load_dotenv
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Core_Functionality.speech_to_text import transcribe_audio
from Core_Functionality.text_to_speech import generate_speech
from Support_Classes.audio_recorder import AudioRecorder
from Framework.langchain_agent import VoiceAgentOrchestrator
from Utils.utils import detect_termination_intent

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"

# Initialize components globally to maintain state across calls
agent = VoiceAgentOrchestrator(OPENAI_API_KEY)

def generate_speech_file(text: str, voice_id: str, output_path: str):
    """Generate speech and save to file"""
    from elevenlabs import ElevenLabs
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    
    audio = client.text_to_speech.convert(
        text=text,
        output_format="mp3_44100_128", 
        voice_id=voice_id, 
        model_id="eleven_multilingual_v2"
    )
    
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    
    return output_path

def start_conversation_gradio():
    if not OPENAI_API_KEY or not ELEVENLABS_API_KEY:
        return [("", "Error: Please set OPENAI_API_KEY and ELEVENLABS_API_KEY in your .env file")], None, ""

    greeting = agent.start_conversation()
    speech_output_path = "./agent_greeting.mp3"
    try:
        generate_speech_file(greeting, ELEVENLABS_VOICE_ID, speech_output_path)
        return [("", greeting)], speech_output_path, ""
    except Exception as e:
        return [("", f"Warning: Could not generate speech for greeting: {e}")], None, ""

def process_input(audio_file, user_text, history):
    if not OPENAI_API_KEY or not ELEVENLABS_API_KEY:
        return history + [("", "Error: Please set OPENAI_API_KEY and ELEVENLABS_API_KEY in your .env file")], None, ""

    user_input = ""
    if audio_file:
        try:
            user_input = transcribe_audio(audio_file, OPENAI_API_KEY)
        except Exception as e:
            return history + [("", f"Error transcribing audio: {e}")], None, ""
    elif user_text:
        user_input = user_text

    if not user_input:
        return history, None, ""

    # Add user input to history
    history.append([user_input, None])

    if detect_termination_intent(user_input):
        farewell = "Thank you for your time. Have a great day!"
        try:
            speech_output_path = "./farewell.mp3"
            generate_speech_file(farewell, ELEVENLABS_VOICE_ID, speech_output_path)
            history[-1][1] = farewell
            summary_data = agent.end_conversation()
            summary_text = "\n--- CONVERSATION SUMMARY ---\n"
            if isinstance(summary_data, dict):
                summary_text += f"Customer: {summary_data.get('customer', 'Unknown')}\n"
                summary_text += f"Sentiment: {summary_data.get('summary', {}).get('sentiment', 'Unknown')}\n"
                summary_text += f"Complaint: {summary_data.get('summary', {}).get('complaint') or 'None'}\n"
                summary_text += f"Database Updated: {summary_data.get('database_updated', 'Unknown')}\n"
            elif isinstance(summary_data, list):
                summary_text += f"Customer: {summary_data[0] if len(summary_data) > 0 else 'Unknown'}\n"
                summary_text += f"Sentiment: {summary_data[1] if len(summary_data) > 1 else 'Unknown'}\n"
                summary_text += f"Complaint: {summary_data[2] if len(summary_data) > 2 else 'None'}\n"
                summary_text += f"Database Updated: {summary_data[3] if len(summary_data) > 3 else 'Unknown'}\n"
            else:
                summary_text += "Unknown summary_data format.\n"
            summary_text += "\nFull conversation history saved to customer database."
            return history, speech_output_path, summary_text
        except Exception as e:
            return history + [("", f"Warning: Could not generate speech or summary: {e}")], None, ""

    response = agent.process_user_input(user_input)
    
    history[-1][1] = response

    try:
        speech_output_path = "./agent_response.mp3"
        generate_speech_file(response, ELEVENLABS_VOICE_ID, speech_output_path)
        return history, speech_output_path, ""
    except Exception as e:
        return history + [("", f"Warning: Could not generate speech: {e}")], None, ""


# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("# AI Voice Agent for Support Follow-Up")
    gr.Markdown("Speak or type your query, and the AI agent will respond. The conversation will end automatically when you express an intent to terminate.")

    chatbot = gr.Chatbot(label="Conversation History", height=400)
    audio_output = gr.Audio(label="Agent Response", autoplay=True)
    summary_display = gr.Textbox(label="Conversation Summary", interactive=False, lines=10)

    with gr.Row():
        audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Your Voice Input", streaming=True)
        text_input = gr.Textbox(label="Your Text Input", placeholder="Type your message here...", lines=3)

    with gr.Row():
        start_btn = gr.Button("Start Conversation", variant="primary")
        clear_btn = gr.Button("Clear All")

    start_btn.click(
        start_conversation_gradio,
        inputs=[],
        outputs=[chatbot, audio_output, summary_display]
    ).then(
        process_input,
        inputs=[audio_input, text_input, chatbot],
        outputs=[chatbot, audio_output, summary_display]
    )

    audio_input.stream(
        process_input,
        inputs=[audio_input, text_input, chatbot],
        outputs=[chatbot, audio_output, summary_display],
        show_progress="full"
    )

    text_input.submit(
        process_input,
        inputs=[audio_input, text_input, chatbot],
        outputs=[chatbot, audio_output, summary_display]
    )

    clear_btn.click(lambda: ([], None, ""), outputs=[chatbot, audio_output, summary_display])

if __name__ == "__main__":
    demo.launch(debug=True)


