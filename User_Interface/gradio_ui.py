import gradio as gr
from elevenlabs import ElevenLabs
import os
from dotenv import load_dotenv
import sys

import numpy as np
import soundfile as sf
from pydub import AudioSegment
from pydub.silence import split_on_silence
import tempfile

# Add your project paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Core_Functionality.speech_to_text import transcribe_audio
from Framework.langchain_agent import VoiceAgentOrchestrator
from Utils.utils import detect_termination_intent

# Load environment variables
load_dotenv()

# API Keys and Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"

# Audio processing constants
SILENCE_THRESHOLD_DB = -40  # dBFS threshold for silence detection
MIN_SILENCE_LEN_MS = 800    # Minimum silence length in milliseconds
MIN_AUDIO_LEN_MS = 500      # Minimum audio length to process
SAMPLE_RATE = 16000         # Standard sample rate for speech processing

# Initialize components globally to maintain state across calls
agent = VoiceAgentOrchestrator(OPENAI_API_KEY) if OPENAI_API_KEY else None

# Global state variables
conversation_active = False
is_recording = False
recorded_audio_data = None

def validate_environment():
    """Validate that all required environment variables are set"""
    missing_keys = []
    
    if not OPENAI_API_KEY:
        missing_keys.append("OPENAI_API_KEY")
    if not ELEVENLABS_API_KEY:
        missing_keys.append("ELEVENLABS_API_KEY")
    
    return missing_keys

def preprocess_audio(audio_data, sample_rate):
    """
    Preprocess audio data to remove silence and normalize
    
    Args:
        audio_data: numpy array of audio samples
        sample_rate: sample rate of the audio
        
    Returns:
        processed audio data or None if audio is too short/silent
    """
    try:
        # Convert to AudioSegment for processing
        # Ensure audio is in the right format (16-bit)
        audio_data_16bit = (audio_data * 32767).astype(np.int16)
        
        # Create temporary file for pydub processing
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            sf.write(tmp_file.name, audio_data_16bit, sample_rate)
            audio_segment = AudioSegment.from_wav(tmp_file.name)
            os.unlink(tmp_file.name)
        
        # Check if audio is too quiet (likely just noise)
        if audio_segment.dBFS < SILENCE_THRESHOLD_DB:
            print(f"Audio too quiet: {audio_segment.dBFS} dBFS")
            return None
        
        # Check minimum duration
        if len(audio_segment) < MIN_AUDIO_LEN_MS:
            print(f"Audio too short: {len(audio_segment)}ms")
            return None
        
        # Split on silence to remove long pauses
        chunks = split_on_silence(
            audio_segment,
            min_silence_len=MIN_SILENCE_LEN_MS,
            silence_thresh=SILENCE_THRESHOLD_DB,
            keep_silence=200  # Keep 200ms of silence for natural speech
        )
        
        if not chunks:
            print("No speech detected after silence removal")
            return None
        
        # Recombine chunks with small silences
        processed_audio = AudioSegment.empty()
        for i, chunk in enumerate(chunks):
            processed_audio += chunk
            # Add small silence between chunks except for the last one
            if i < len(chunks) - 1:
                processed_audio += AudioSegment.silent(duration=100)
        
        # Normalize audio levels
        processed_audio = processed_audio.normalize()
        
        # Convert back to numpy array
        samples = processed_audio.get_array_of_samples()
        processed_data = np.array(samples).astype(np.float32) / 32768.0
        
        return processed_data
        
    except Exception as e:
        print(f"Error preprocessing audio: {e}")
        return audio_data  # Return original if processing fails

def generate_speech_file(text: str, voice_id: str, output_path: str):
    """
    Generate speech using ElevenLabs API and save to file
    
    Args:
        text: Text to convert to speech
        voice_id: ElevenLabs voice ID
        output_path: Path to save the audio file
        
    Returns:
        Path to generated audio file or None if failed
    """
    try:
        if not ELEVENLABS_API_KEY:
            print("Warning: ElevenLabs API key not set, skipping speech generation")
            return None
            
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        
        # Generate speech with high quality settings
        audio = client.text_to_speech.convert(
            text=text,
            output_format="mp3_44100_128", 
            voice_id=voice_id, 
            model_id="eleven_multilingual_v2"
        )
        
        # Save to file
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        
        print(f"Generated speech: {len(text)} characters -> {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error generating speech: {e}")
        return None

def start_conversation():
    """
    Initialize and start a new conversation with the agent
    
    Returns:
        Tuple: (chat_history, audio_file, summary, recording_button_state)
    """
    global conversation_active, is_recording, agent
    
    # Validate environment
    missing_keys = validate_environment()
    if missing_keys:
        error_msg = f"Missing required API keys: {', '.join(missing_keys)}"
        return [("System", f"Error: {error_msg}")], None, "", gr.Button(interactive=False)
    
    if not agent:
        return [("System", "Error: Agent not initialized properly")], None, "", gr.Button(interactive=False)

    # Reset state
    conversation_active = True
    is_recording = False

    try:
        # Get greeting from agent
        greeting = agent.start_conversation()
        speech_output_path = "./agent_greeting.mp3"
        
        # Generate speech for greeting
        audio_file = generate_speech_file(greeting, ELEVENLABS_VOICE_ID, speech_output_path)
        
        chat_history = [("Agent", greeting)]
        
        # Enable recording button after agent speaks
        return chat_history, audio_file, "", gr.Button("🎤 Start Recording", interactive=True, variant="primary")
        
    except Exception as e:
        error_msg = f"Error starting conversation: {e}"
        print(error_msg)
        return [("System", error_msg)], None, "", gr.Button(interactive=False)

def start_recording():
    """
    Start recording user's voice input
    
    Returns:
        Updated recording button state
    """
    global is_recording
    
    if not conversation_active:
        return gr.Button("🎤 Start Recording", interactive=False)
    
    is_recording = True
    print("Recording started...")
    
    return gr.Button("⏹️ Stop Recording", interactive=True, variant="stop")

def stop_recording_and_process(audio_data, chat_history):
    """
    Stop recording and process the recorded audio
    
    Args:
        audio_data: Recorded audio data from Gradio
        chat_history: Current conversation history
        
    Returns:
        Tuple: (updated_chat_history, audio_response, summary, recording_button_state)
    """
    global is_recording, conversation_active
    
    is_recording = False
    
    if not conversation_active:
        return chat_history, None, "", gr.Button(interactive=False)
    
    if audio_data is None:
        print("No audio data received")
        return chat_history, None, "", gr.Button("🎤 Start Recording", interactive=True, variant="primary")
    
    try:
        sample_rate, audio_array = audio_data
        print(f"Processing audio: {len(audio_array)} samples at {sample_rate}Hz")
        
        # Preprocess audio to remove silence and normalize
        processed_audio = preprocess_audio(audio_array, sample_rate)
        
        if processed_audio is None:
            print("Audio preprocessing returned None - likely too quiet or short")
            return chat_history, None, "", gr.Button("🎤 Start Recording", interactive=True, variant="primary")
        
        # Save processed audio to temporary file for transcription
        temp_audio_file = "./temp_user_input.wav"
        sf.write(temp_audio_file, processed_audio, sample_rate)
        
        # Transcribe audio to text
        user_input = transcribe_audio(temp_audio_file, OPENAI_API_KEY)
        
        # Clean up temporary file
        if os.path.exists(temp_audio_file):
            os.remove(temp_audio_file)
        
        print(f"Transcribed text: '{user_input}'")
        
        # Check if transcription was successful and meaningful
        if not user_input or len(user_input.strip()) < 2:
            print("Transcription failed or too short")
            return chat_history, None, "", gr.Button("🎤 Start Recording", interactive=True, variant="primary")
        
        # Process the transcribed input
        return process_user_input_internal(user_input, chat_history)
        
    except Exception as e:
        error_msg = f"Error processing audio: {e}"
        print(error_msg)
        updated_history = chat_history + [("System", error_msg)]
        return updated_history, None, "", gr.Button("🎤 Start Recording", interactive=True, variant="primary")

def process_user_input_internal(user_input, chat_history):
    """
    Process user input and generate agent response
    
    Args:
        user_input: User's input text
        chat_history: Current conversation history
        
    Returns:
        Tuple: (updated_chat_history, audio_response, summary, recording_button_state)
    """
    global conversation_active, agent
    
    # Add user input to chat history
    updated_history = chat_history + [("User", user_input)]
    
    # Check for conversation termination intent
    if detect_termination_intent(user_input):
        return handle_conversation_end(updated_history)
    
    # Get agent response
    try:
        response = agent.process_user_input(user_input) # type: ignore
        updated_history.append(("Agent", response))
        
        # Generate speech for agent response
        speech_output_path = "./agent_response.mp3"
        audio_file = generate_speech_file(response, ELEVENLABS_VOICE_ID, speech_output_path)
        
        print(f"Agent response: '{response[:100]}...' (audio: {audio_file is not None})")
        
        # Enable recording for next user input
        return updated_history, audio_file, "", gr.Button("🎤 Start Recording", interactive=True, variant="primary")
        
    except Exception as e:
        error_msg = f"Error processing input: {e}"
        print(error_msg)
        updated_history.append(("System", error_msg))
        return updated_history, None, "", gr.Button("🎤 Start Recording", interactive=True, variant="primary")

def handle_conversation_end(chat_history):
    """
    Handle conversation termination and generate summary
    
    Args:
        chat_history: Current conversation history
        
    Returns:
        Tuple: (updated_chat_history, farewell_audio, summary, recording_button_state)
    """
    global conversation_active, agent
    
    farewell = "Thank you for your time. Have a great day!"
    
    try:
        # Generate farewell speech
        speech_output_path = "./farewell.mp3"
        audio_file = generate_speech_file(farewell, ELEVENLABS_VOICE_ID, speech_output_path)
        
        updated_history = chat_history + [("Agent", farewell)]
        
        # Generate conversation summary
        summary_data = agent.end_conversation() # type: ignore
        summary_text = format_conversation_summary(summary_data)
        
        # Mark conversation as ended
        conversation_active = False
        
        print("Conversation ended successfully")
        return updated_history, audio_file, summary_text, gr.Button("Conversation Ended", interactive=False)
        
    except Exception as e:
        error_msg = f"Error ending conversation: {e}"
        print(error_msg)
        updated_history = chat_history + [("System", error_msg)]
        conversation_active = False
        return updated_history, None, "", gr.Button("Error - Restart Required", interactive=False)

def format_conversation_summary(summary_data):
    """
    Format conversation summary data for display
    
    Args:
        summary_data: Summary data from agent
        
    Returns:
        Formatted summary string
    """
    summary_text = "\n--- CONVERSATION SUMMARY ---\n"
    
    try:
        if isinstance(summary_data, dict):
            summary_text += f"Customer: {summary_data.get('customer', 'Unknown')}\n"
            summary_text += f"Sentiment: {summary_data.get('summary', {}).get('sentiment', 'Unknown')}\n"
            summary_text += f"Complaint: {summary_data.get('summary', {}).get('complaint') or 'None'}\n"
            summary_text += f"Database Updated: {summary_data.get('database_updated', 'Unknown')}\n"
        elif isinstance(summary_data, list) and len(summary_data) >= 4:
            summary_text += f"Customer: {summary_data[0]}\n"
            summary_text += f"Sentiment: {summary_data[1]}\n"
            summary_text += f"Complaint: {summary_data[2]}\n"
            summary_text += f"Database Updated: {summary_data[3]}\n"
        else:
            summary_text += "Summary data not available.\n"
            
        summary_text += "\nFull conversation history saved to customer database."
        
    except Exception as e:
        summary_text += f"Error formatting summary: {e}"
    
    return summary_text

def process_text_input(text_input, chat_history):
    """
    Process text input as alternative to voice input
    
    Args:
        text_input: User's text input
        chat_history: Current conversation history
        
    Returns:
        Tuple: (updated_chat_history, audio_response, summary, cleared_text_input, recording_button_state)
    """
    global conversation_active
    
    if not text_input or not conversation_active:
        return chat_history, None, "", "", gr.Button("🎤 Start Recording", interactive=conversation_active, variant="primary")
    
    # Process the text input
    result_history, audio_file, summary, button_state = process_user_input_internal(text_input, chat_history)
    
    # Clear text input after processing
    return result_history, audio_file, summary, "", button_state

def clear_all():
    """
    Clear all conversation data and reset the interface
    
    Returns:
        Tuple of cleared/reset interface elements
    """
    global conversation_active, is_recording
    
    conversation_active = False
    is_recording = False
    
    print("Interface cleared and reset")
    
    return [], None, "", "", gr.Button("🎤 Start Recording", interactive=False)

# Create Gradio Interface
with gr.Blocks(theme=gr.themes.Soft(), title="AI Voice Agent") as demo:
    gr.Markdown("# 🎙️ AI Voice Agent for Support Follow-Up")
    gr.Markdown("""
    **Instructions:**
    1. Click **Start Conversation** to begin
    2. The agent will greet you with voice
    3. Click **Start Recording** to record your response
    4. Click **Stop Recording** when you're done speaking
    5. The agent will process your input and respond
    6. You can also type messages as an alternative to voice input
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            # Conversation display
            chatbot = gr.Chatbot(
                label="Conversation History", 
                height=450,
                type="tuples",
                show_label=True,
                show_copy_button=True
            )
        
        with gr.Column(scale=1):
            # Audio output for agent responses
            audio_output = gr.Audio(
                label="🔊 Agent Response", 
                autoplay=True,
                show_label=True,
                interactive=False
            )
            
            # Conversation summary display
            summary_display = gr.Textbox(
                label="📋 Conversation Summary", 
                interactive=False, 
                lines=10,
                show_label=True,
                max_lines=15
            )
    
    with gr.Row():
        # Voice input section
        with gr.Column(scale=2):
            # Audio recording input
            audio_input = gr.Audio(
                sources=["microphone"], 
                type="numpy", 
                label="🎤 Voice Input",
                show_label=True,
                interactive=True
            )
            
            # Recording control button
            record_button = gr.Button(
                "🎤 Start Recording", 
                interactive=False,
                variant="primary",
                size="lg"
            )
        
        with gr.Column(scale=1):
            # Text input as alternative
            text_input = gr.Textbox(
                label="💬 Type your message (alternative to voice)", 
                placeholder="Type your message here...",
                lines=3,
                max_lines=5
            )
    
    with gr.Row():
        start_btn = gr.Button(
            "🚀 Send Recorded Voice", 
            variant="primary", 
            size="lg",
            scale=1
        )
        clear_btn = gr.Button(
            "🗑️ Clear All", 
            variant="secondary",
            scale=1
        )
    
    # Event Handlers
    
    # Start conversation
    start_btn.click(
        start_conversation,
        inputs=[],
        outputs=[chatbot, audio_output, summary_display, record_button]
    )
    
    # Recording button toggle functionality
    def toggle_recording(audio_data, chat_history):
        """Toggle between start and stop recording based on current state"""
        global is_recording
        
        if not is_recording:
            return start_recording()
        else:
            return stop_recording_and_process(audio_data, chat_history)
    
    # Handle recording button clicks
    record_button.click(
        lambda: start_recording() if not is_recording else None,
        outputs=[record_button]
    ).then(
        lambda audio_data, chat_history: stop_recording_and_process(audio_data, chat_history) if is_recording else (chat_history, None, "", record_button),
        inputs=[audio_input, chatbot],
        outputs=[chatbot, audio_output, summary_display, record_button]
    )
    
    # Text input processing
    text_input.submit(
        process_text_input,
        inputs=[text_input, chatbot],
        outputs=[chatbot, audio_output, summary_display, text_input, record_button]
    )
    
    # Clear all functionality
    clear_btn.click(
        clear_all,
        inputs=[],
        outputs=[chatbot, audio_output, summary_display, text_input, record_button]
    )

# Launch the application
if __name__ == "__main__":
    print("Starting AI Voice Agent...")
    print("Make sure your .env file contains:")
    print("- OPENAI_API_KEY")
    print("- ELEVENLABS_API_KEY")
    
    demo.launch(
        share=False, 
        show_error=True,
        debug = True,
        # server_name="0.0.0.0",  # Allow access from other devices on network
        # server_port=7860,
        # show_api=False
    )