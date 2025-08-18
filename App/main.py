import os
from dotenv import load_dotenv
import sys

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

def run_ai_voice_agent():
    """Main function to run the AI Voice Agent"""
    print("=== AI Voice Agent for Support Follow-Up ===")
    print("Initializing...")

    # Validate API keys
    if not OPENAI_API_KEY or not ELEVENLABS_API_KEY:
        print("Error: Please set OPENAI_API_KEY and ELEVENLABS_API_KEY in your .env file")
        return

    # Initialize components
    agent = VoiceAgentOrchestrator(OPENAI_API_KEY)
    audio_recorder = AudioRecorder()
    
    print("Agent initialized successfully!")
    
    # Choose input mode
    print("\nSelect input mode:")
    print("1. Text input (for testing)")
    print("2. Voice input (requires microphone)")
    
    mode = input("Enter choice (1 or 2): ").strip()
    use_voice = mode == "2"
    
    if use_voice:
        print("Voice mode selected. Make sure your microphone is working.")
    else:
        print("Text mode selected.")

    # Start conversation
    print("\n" + "="*50)
    greeting = agent.start_conversation()
    print(f"Agent: {greeting}")
    
    # Generate speech for greeting
    try:
        speech_output_path = "./agent_greeting.mp3"
        generate_speech(greeting, ELEVENLABS_VOICE_ID)
    except Exception as e:
        print(f"Warning: Could not generate speech: {e.body}") # type: ignore

    # Main conversation loop
    conversation_active = True
    while conversation_active:
        try:
            # Get user input
            if use_voice:
                print("\nListening... (speak now)")
                audio_file = audio_recorder.record_until_silence()
                if audio_file:
                    try:
                        user_input = transcribe_audio(audio_file, OPENAI_API_KEY)
                        print(f"You said: {user_input}")
                    except Exception as e:
                        print(f"Error transcribing audio: {e}")
                        continue
                else:
                    print("No audio recorded. Please try again.")
                    continue
            else:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue

            # Check for termination intent
            if detect_termination_intent(user_input):
                print("\nDetected end-of-call intent. Wrapping up...")
                farewell = "Thank you for your time. Have a great day!"
                print(f"Agent: {farewell}")
                try:
                    speech_output_path = "./farewell.mp3"
                    generate_speech(farewell, ELEVENLABS_VOICE_ID)
                except Exception as e:
                    print(f"Warning: Could not generate speech: {e.body}") # type: ignore
                conversation_active = False
                break

            # Process with LangChain agent
            response = agent.process_user_input(user_input)
            print(f"Agent: {response}")
            
            # Generate speech response
            try:
                speech_output_path = "./agent_response.mp3"
                generate_speech(response, ELEVENLABS_VOICE_ID)
            except Exception as e:
                print(f"Warning: Could not generate speech: {e.body}")  # type: ignore

        except KeyboardInterrupt:
            print("\n\nConversation interrupted by user.")
            conversation_active = False
        except Exception as e:
            print(f"Error during conversation: {e}")
            error_response = "I apologize, but I'm experiencing some technical difficulties. Could you please try again?"
            print(f"Agent: {error_response}")
            try:
                speech_output_path = "./error_response.mp3"
                generate_speech(error_response, ELEVENLABS_VOICE_ID)
            except:
                pass

    # End conversation and generate summary
    print("\n" + "="*50)
    print("Ending conversation...")
    
    try:
        summary_data = agent.end_conversation()
        print("\n--- CONVERSATION SUMMARY ---")
        # If summary_data is a dictionary, keep as is; if it's a list, use indices
        if isinstance(summary_data, dict):
            print(f"Customer: {summary_data.get('customer', 'Unknown')}")
            print(f"Sentiment: {summary_data.get('summary', {}).get('sentiment', 'Unknown')}")
            print(f"Complaint: {summary_data.get('summary', {}).get('complaint') or 'None'}")
            print(f"Database Updated: {summary_data.get('database_updated', 'Unknown')}")
        elif isinstance(summary_data, list):
            print(f"Customer: {summary_data[0] if len(summary_data) > 0 else 'Unknown'}")
            print(f"Sentiment: {summary_data[1] if len(summary_data) > 1 else 'Unknown'}")
            print(f"Complaint: {summary_data[2] if len(summary_data) > 2 else 'None'}")
            print(f"Database Updated: {summary_data[3] if len(summary_data) > 3 else 'Unknown'}")
        else:
            print("Unknown summary_data format.")
        print("\nFull conversation history saved to customer database.")
    except Exception as e:
        print(f"Error generating summary: {e}")

    print("\nThank you for using the AI Voice Agent!")

if __name__ == "__main__":
    run_ai_voice_agent() 