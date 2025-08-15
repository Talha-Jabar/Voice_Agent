import gradio as gr
import os
from dotenv import load_dotenv
import sys
import json
import tempfile
import threading
import time
from typing import Optional, Tuple, List

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

# Global state management
class ConversationState:
    def __init__(self):
        self.agent = None
        self.audio_recorder = AudioRecorder()
        self.conversation_active = False
        self.conversation_history = []
        
    def initialize_agent(self):
        """Initialize the agent if not already done"""
        if not self.agent and OPENAI_API_KEY:
            self.agent = VoiceAgentOrchestrator(OPENAI_API_KEY)

# Global state instance
state = ConversationState()

def generate_speech_file(text: str, voice_id: str, output_path: str) -> Optional[str]:
    """Generate speech and save to file"""
    try:
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
    except Exception as e:
        print(f"Error generating speech: {e}")
        return None

def start_conversation():
    """Start a new conversation"""
    if not OPENAI_API_KEY or not ELEVENLABS_API_KEY:
        error_msg = "❌ Error: Please set OPENAI_API_KEY and ELEVENLABS_API_KEY in your .env file"
        return [], error_msg, "❌ Configuration Error"
    
    try:
        # Initialize agent if needed
        state.initialize_agent()
        
        if not state.agent:
            error_msg = "❌ Error: Could not initialize AI agent"
            return [], None, error_msg, "❌ Agent Error"
        
        # Reset state
        state.conversation_history = []
        state.conversation_active = True
        
        # Start conversation with agent
        greeting = state.agent.start_conversation()
        state.conversation_history.append(["", greeting])
        
        # Generate speech for greeting
        speech_output_path = "./agent_greeting.mp3"
        audio_file = generate_speech_file(greeting, ELEVENLABS_VOICE_ID, speech_output_path)
        
        success_msg = "🤖 Conversation started! The agent is speaking. After the audio finishes, click 'Record Voice Input' to respond."
        
        return (
            state.conversation_history,
            audio_file,
            success_msg,
            "🎤 Ready to Listen"
        )
        
    except Exception as e:
        error_msg = f"❌ Error starting conversation: {e}"
        return [], None, error_msg, "❌ Error"

def record_and_process_voice():
    """Record voice input and process it"""
    if not state.conversation_active:
        return (
            state.conversation_history,
            None,
            "❌ No active conversation. Please start a conversation first.",
            "❌ No Active Conversation"
        )
    
    try:
        # Update UI to show recording status
        yield (
            state.conversation_history,
            None,
            "🎤 Recording... Please speak now. The system will automatically stop when you finish.",
            "🎤 Recording..."
        )
        
        # Record audio with silence detection
        audio_file = state.audio_recorder.record_until_silence(
            filename=f"./user_input.wav",
            rms_silence_threshold=0.01,
            silence_duration=3,  # Wait 3 seconds of silence
            max_duration=5      # Max 30 seconds
        )
        
        if not audio_file or not os.path.exists(audio_file):
            yield (
                state.conversation_history,
                None,
                "❌ No speech detected. Please try again.",
                "🎤 Ready to Listen"
            )
            return
        
        # Update UI to show processing
        yield (
            state.conversation_history,
            None,
            "🔄 Processing your speech...",
            "🔄 Processing..."
        )
        
        # Transcribe audio
        user_input = transcribe_audio(audio_file, OPENAI_API_KEY)
        
        if not user_input.strip():
            # Clean up and return
            try:
                os.remove(audio_file)
            except:
                pass
            yield (
                state.conversation_history,
                None,
                "❌ Could not understand speech. Please try again.",
                "🎤 Ready to Listen"
            )
            return
        
        # Add user input to history
        state.conversation_history.append([user_input, ""])
        
        yield (
            state.conversation_history,
            None,
            f"✅ You said: '{user_input}'\n🤖 Agent is thinking...",
            "🤖 Thinking..."
        )
        
        # Check for termination intent
        if detect_termination_intent(user_input):
            # Handle conversation end
            farewell = "Thank you for your time. Have a great day!"
            state.conversation_history[-1][1] = farewell
            
            # Generate farewell speech
            speech_output_path = "./farewell.mp3"
            audio_file_response = generate_speech_file(farewell, ELEVENLABS_VOICE_ID, speech_output_path)
            
            # Get summary
            summary_data = state.agent.end_conversation()
            summary_text = format_summary(summary_data)
            
            state.conversation_active = False
            
            # Clean up input audio file
            try:
                os.remove(audio_file)
            except:
                pass
            
            yield (
                state.conversation_history,
                audio_file_response,
                f"👋 Conversation ended.\n\n{summary_text}",
                "✅ Conversation Complete"
            )
            return
        
        # Process with agent
        response = state.agent.process_user_input(user_input)
        
        # Update history with agent response
        state.conversation_history[-1][1] = response
        
        yield (
            state.conversation_history,
            None,
            "🔊 Agent is responding...",
            "🔊 Speaking..."
        )
        
        # Generate speech response
        speech_output_path = f"./agent_response.mp3"
        audio_file_response = generate_speech_file(response, ELEVENLABS_VOICE_ID, speech_output_path)
        
        # Clean up input audio file
        try:
            os.remove(audio_file)
        except:
            pass
        
        final_message = "✅ Agent responded! After listening to the response, click 'Record Voice Input' again to continue the conversation."
        
        yield (
            state.conversation_history,
            audio_file_response,
            final_message,
            "🎤 Ready to Listen"
        )
        
    except Exception as e:
        # Clean up on error
        try:
            if 'audio_file' in locals() and os.path.exists(audio_file):
                os.remove(audio_file)
        except:
            pass
        
        yield (
            state.conversation_history,
            None,
            f"❌ Error: {e}",
            "❌ Error"
        )

def process_text_input(text_input: str):
    """Process text input from the user"""
    if not text_input.strip():
        return (
            state.conversation_history,
            None,
            "❌ Please enter some text.",
            "🎤 Ready to Listen",
            ""
        )
    
    if not state.conversation_active:
        return (
            state.conversation_history,
            None,
            "❌ No active conversation. Please start a conversation first.",
            "❌ No Active Conversation",
            ""
        )
    
    try:
        # Add user input to history
        state.conversation_history.append([text_input, ""])
        
        # Check for termination intent
        if detect_termination_intent(text_input):
            # Handle conversation end
            farewell = "Thank you for your time. Have a great day!"
            state.conversation_history[-1][1] = farewell
            
            # Generate farewell speech
            speech_output_path = "./farewell.mp3"
            audio_file_response = generate_speech_file(farewell, ELEVENLABS_VOICE_ID, speech_output_path)
            
            # Get summary
            summary_data = state.agent.end_conversation()
            summary_text = format_summary(summary_data)
            
            state.conversation_active = False
            
            return (
                state.conversation_history,
                audio_file_response,
                f"👋 Conversation ended.\n\n{summary_text}",
                "✅ Conversation Complete",
                ""
            )
        
        # Process with agent
        response = state.agent.process_user_input(text_input)
        
        # Update history with agent response
        state.conversation_history[-1][1] = response
        
        # Generate speech response
        speech_output_path = f"./agent_response.mp3"
        audio_file_response = generate_speech_file(response, ELEVENLABS_VOICE_ID, speech_output_path)
        
        success_message = "✅ Text processed! Agent responded."
        
        return (
            state.conversation_history,
            audio_file_response,
            success_message,
            "🎤 Ready to Listen",
            ""  # Clear text input
        )
        
    except Exception as e:
        return (
            state.conversation_history,
            None,
            f"❌ Error processing text: {e}",
            "❌ Error",
            text_input  # Keep text input on error
        )

def format_summary(summary_data) -> str:
    """Format conversation summary"""
    summary_text = "📋 CONVERSATION SUMMARY\n" + "="*50 + "\n"
    
    if isinstance(summary_data, dict):
        summary_text += f"👤 Customer: {summary_data.get('customer', 'Unknown')}\n"
        summary_text += f"😊 Sentiment: {summary_data.get('summary', {}).get('sentiment', 'Unknown')}\n"
        summary_text += f"❗ Complaint: {summary_data.get('summary', {}).get('complaint') or 'None'}\n"
        summary_text += f"💾 Database Updated: {summary_data.get('database_updated', 'Unknown')}\n"
    elif isinstance(summary_data, list):
        summary_text += f"👤 Customer: {summary_data[0] if len(summary_data) > 0 else 'Unknown'}\n"
        summary_text += f"😊 Sentiment: {summary_data[1] if len(summary_data) > 1 else 'Unknown'}\n"
        summary_text += f"❗ Complaint: {summary_data[2] if len(summary_data) > 2 else 'None'}\n"
        summary_text += f"💾 Database Updated: {summary_data[3] if len(summary_data) > 3 else 'Unknown'}\n"
    else:
        summary_text += "❓ Unknown summary format.\n"
        
    summary_text += "\n✅ Full conversation history saved to customer database."
    return summary_text

def stop_conversation():
    """Stop the current conversation"""
    state.conversation_active = False
    return (
        state.conversation_history,
        None,
        "⏹️ Conversation stopped by user.",
        "⏹️ Stopped"
    )

def clear_all():
    """Clear all conversation data"""
    state.conversation_active = False
    state.conversation_history = []
    return (
        [],
        None,
        "🗑️ All data cleared.",
        "🗑️ Cleared",
        ""
    )

# Create the Gradio interface
with gr.Blocks(
    title="AI Voice Agent - RichDaddy Support",
    theme=gr.themes.Soft(),
    css="""
    .status-box {
        background: linear-gradient(45deg, #f0f8ff, #e6f3ff);
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    """
) as demo:
    
    gr.Markdown("# 🤖 AI Voice Agent for Customer Support Follow-Up")
    
    with gr.Row():
        gr.Markdown("""
        ### 📋 Instructions:
        1. **Start Conversation**: Click to begin a new customer support call
        2. **Voice Input**: After the agent speaks, click "Record Voice Input" to respond
        3. **Automatic Detection**: The system detects when you stop speaking and processes your input
        4. **Text Option**: You can also type responses instead of speaking
        5. **Natural Flow**: Conversation continues until you say goodbye or similar phrases
        """)
    
    # Main conversation area
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                label="💬 Conversation",
                height=400,
                bubble_full_width=False,
                show_copy_button=True
            )
        
        with gr.Column(scale=1):
            status_display = gr.Textbox(
                label="📊 Status",
                value="Ready to Start",
                interactive=False,
                lines=2,
                elem_classes="status-box"
            )
    
    # Audio output for agent responses
    audio_output = gr.Audio(
        label="🔊 Agent Response Audio",
        autoplay=True,
        show_download_button=True
    )
    
    # System messages
    system_message = gr.Textbox(
        label="📢 System Messages",
        value="Welcome! Click 'Start Conversation' to begin.",
        interactive=False,
        lines=4
    )
    
    # Main control buttons
    with gr.Row():
        start_btn = gr.Button(
            "🚀 Start Conversation",
            variant="primary",
            scale=2,
            size="lg"
        )
        record_btn = gr.Button(
            "🎤 Record Voice Input",
            variant="secondary",
            scale=2,
            size="lg"
        )
    
    # Text input area
    with gr.Row():
        text_input = gr.Textbox(
            label="💬 Or Type Your Message",
            placeholder="Type your response here...",
            lines=2,
            scale=4
        )
        send_text_btn = gr.Button(
            "📤 Send Text",
            variant="secondary",
            scale=1
        )
    
    # Additional control buttons
    with gr.Row():
        stop_btn = gr.Button("⏹️ Stop Conversation", variant="stop")
        clear_btn = gr.Button("🗑️ Clear All", variant="secondary")
    
    # Event handlers
    
    # Start conversation
    start_btn.click(
        fn=start_conversation,
        inputs=[],
        outputs=[chatbot, audio_output, system_message, status_display]
    )
    
    # Record and process voice input (with streaming)
    record_btn.click(
        fn=record_and_process_voice,
        inputs=[],
        outputs=[chatbot, audio_output, system_message, status_display]
    )
    
    # Process text input
    send_text_btn.click(
        fn=process_text_input,
        inputs=[text_input],
        outputs=[chatbot, audio_output, system_message, status_display, text_input]
    )
    
    # Submit text with Enter key
    text_input.submit(
        fn=process_text_input,
        inputs=[text_input],
        outputs=[chatbot, audio_output, system_message, status_display, text_input]
    )
    
    # Stop conversation
    stop_btn.click(
        fn=stop_conversation,
        inputs=[],
        outputs=[chatbot, audio_output, system_message, status_display]
    )
    
    # Clear all
    clear_btn.click(
        fn=clear_all,
        inputs=[],
        outputs=[chatbot, audio_output, system_message, status_display, text_input]
    )
    
    # Add some helpful information at the bottom
    with gr.Accordion("ℹ️ Additional Information", open=False):
        gr.Markdown("""
        ### 🎯 Features:
        - **Automatic Speech Recognition**: Uses OpenAI Whisper for accurate transcription
        - **Natural Language Processing**: Powered by GPT-4o-mini for intelligent responses
        - **Text-to-Speech**: ElevenLabs for natural-sounding voice responses
        - **Silence Detection**: Automatically detects when you finish speaking
        - **Customer Database**: Updates customer records based on conversation
        - **Conversation Summaries**: Generates detailed summaries at conversation end
        
        ### 🔧 Technical Requirements:
        - **Python**: 3.11 or higher
        - **API Keys**: OpenAI and ElevenLabs API keys required
        - **Audio**: Microphone for voice input, speakers for audio output
        - **System**: Works best on Linux/Ubuntu systems
        
        ### 🎤 Voice Input Tips:
        - Speak clearly and at normal volume
        - Wait for silence detection (3 seconds of quiet)
        - Maximum recording time is 30 seconds
        - If no speech is detected, try again
        - Use "goodbye", "bye", or "end call" to terminate
        
        ### 💡 Troubleshooting:
        - If voice recording fails, use text input as backup
        - Check microphone permissions if audio issues occur
        - Ensure API keys are properly configured in .env file
        - System messages will show detailed error information
        """)

if __name__ == "__main__":
    print("🚀 Starting AI Voice Agent Interface...")
    print("📋 Checking system requirements...")
    
    # Check API keys
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in environment variables")
    else:
        print("✅ OpenAI API key configured")
    
    if not ELEVENLABS_API_KEY:
        print("❌ ELEVENLABS_API_KEY not found in environment variables")
    else:
        print("✅ ElevenLabs API key configured")
    
    # Launch interface
    demo.launch(
        debug=True,
        show_error=True,
    )