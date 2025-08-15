# AI Voice Agent for Support Follow-Up

A comprehensive Speech-to-Speech AI Voice Agent designed for customer support follow-up calls. This agent leverages OpenAI's Whisper for speech-to-text, GPT-4o-mini for intelligent conversation processing, and ElevenLabs for natural text-to-speech synthesis, all orchestrated through LangChain.

## Features

### Core Functionality
- **Speech-to-Text**: Converts customer voice input using OpenAI's Whisper-1 model
- **Intelligent Processing**: Uses GPT-4o-mini for natural language understanding and response generation
- **Text-to-Speech**: Generates natural speech responses using ElevenLabs' eleven_multilingual_v2 model
- **Conversation Management**: Maintains context throughout the entire conversation
- **Customer Database**: JSON-based customer database with comprehensive customer information
- **LangChain Orchestration**: Seamless integration of multiple AI tools and functions

### Advanced Features
- **Termination Detection**: Automatically detects when customers want to end the call
- **Sentiment Analysis**: Analyzes customer sentiment throughout the conversation
- **Complaint Handling**: Records and tracks customer complaints with unique ticket IDs
- **Database Updates**: Automatically updates customer records with conversation outcomes
- **Conversation Summarization**: Generates detailed summaries at the end of each call

## Project Structure

```
ai_voice_agent/
├──
├── main.py                    # Main application entry point
├── .env                       # Environment variables (API keys)
├── requirements.txt           # Python dependencies
├── customer_database.py       # Customer database management
├── customer_database.json     # JSON database file (auto-generated)
├── speech_to_text.py         # OpenAI Whisper integration
├── text_to_speech.py         # ElevenLabs TTS integration
├── audio_recorder.py         # Audio recording functionality
├── langchain_agent.py        # LangChain agent orchestration
├── conversation_manager.py   # Conversation history management
├── prompt_templates.py       # AI prompt templates
├── utils.py                  # Utility functions
├── test_basic_functionality.py # Basic functionality tests
├── demo_text_mode.py         # Text-only demo script
└── README.md                 # This documentation
```

## Installation

### Prerequisites
- Python 3.11 or higher
- Ubuntu/Linux system (for audio dependencies)
- OpenAI API key
- ElevenLabs API key (optional for text-only mode)

### System Dependencies
```bash
sudo apt-get update
sudo apt-get install -y build-essential portaudio19-dev python3-dev python3.11-dev
```

### Python Dependencies
```bash
pip install -r requirements.txt
```

### API Key Configuration
1. Copy the `.env` file and add your API keys:
```bash
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

## Usage

### Quick Start (Text Mode)
For testing without audio dependencies:
```bash
python3 demo_text_mode.py
```

### Full Voice Mode
For complete speech-to-speech functionality:
```bash
python3 main.py
```

### Running Tests
To verify installation and basic functionality:
```bash
python3 test_basic_functionality.py
```

## Configuration

### Customer Database
The system automatically creates a dummy customer database for RichDaddy Incorporation with 5 sample customers. Each customer record includes:

- Customer ID and name
- Product orders and order IDs
- Location and delivery information
- Payment status and methods
- Complaint tracking
- Conversation history
- Sentiment analysis results

### Voice Configuration
The default voice uses ElevenLabs voice ID `f5HLTX707KIM4SzJYzSz` with the `eleven_multilingual_v2` model. This can be modified in `text_to_speech.py`.

### Conversation Flow
1. Agent selects a random customer from the database
2. Initiates conversation with personalized greeting
3. Processes customer responses using LangChain tools
4. Handles complaints and updates database accordingly
5. Detects conversation termination intent
6. Generates summary and updates customer records

## Technical Architecture

### LangChain Integration
The system uses LangChain for intelligent tool orchestration, including:
- Customer information retrieval
- Database updates
- Complaint recording
- Conversation history management

### Audio Processing
- **Recording**: Uses sounddevice for real-time audio capture
- **Transcription**: OpenAI Whisper-1 for accurate speech-to-text
- **Synthesis**: ElevenLabs for natural-sounding speech output

### Error Handling
Comprehensive error handling ensures graceful degradation:
- API failures fall back to text-only mode
- Audio issues prompt user for text input
- Database errors are logged and reported

## Troubleshooting

### Common Issues

**Audio Dependencies**
If you encounter PyAudio installation issues:
```bash
sudo apt-get install portaudio19-dev python3.11-dev
pip install pyaudio
```

**API Key Issues**
Ensure your `.env` file contains valid API keys:
- OpenAI API key is required for all functionality
- ElevenLabs API key is optional (text-only mode available)

**Permission Issues**
For microphone access, ensure proper permissions:
```bash
sudo usermod -a -G audio $USER
```

### Testing Without Audio
Use the text-only demo for testing core functionality:
```bash
python3 demo_text_mode.py
```

## Development

### Adding New Features
The modular architecture allows easy extension:
- Add new tools in `langchain_agent.py`
- Extend customer database schema in `customer_database.py`
- Modify conversation flow in `main.py`

### Customization
- **Company Information**: Update company name and details in prompt templates
- **Voice Selection**: Modify voice ID in `text_to_speech.py`
- **Database Schema**: Extend customer fields in `customer_database.py`

## License

This project is provided as-is for educational and development purposes.

## Support

For issues and questions, please refer to the troubleshooting section or check the test scripts for diagnostic information.

