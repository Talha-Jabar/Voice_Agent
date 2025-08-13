# Technical Documentation - AI Voice Agent

## Architecture Overview

The AI Voice Agent is built using a modular architecture that separates concerns and allows for easy maintenance and extension. The system integrates multiple AI services through LangChain orchestration to provide a seamless speech-to-speech customer support experience.

### Core Components

#### 1. Audio Processing Pipeline
- **Input**: Real-time audio capture via `sounddevice`
- **Processing**: OpenAI Whisper-1 for speech-to-text conversion
- **Output**: ElevenLabs TTS for speech synthesis

#### 2. Language Model Integration
- **Primary LLM**: GPT-4o-mini for conversation processing
- **Orchestration**: LangChain for tool management and workflow
- **Context Management**: Conversation history and customer data integration

#### 3. Data Management
- **Customer Database**: JSON-based storage with CRUD operations
- **Conversation History**: In-memory management with persistence
- **State Management**: Session-based conversation tracking

## Module Documentation

### main.py
**Purpose**: Application entry point and main conversation loop

**Key Functions**:
- `run_ai_voice_agent()`: Main application orchestrator
- Input mode selection (text vs. voice)
- Error handling and graceful degradation
- Conversation flow management

**Dependencies**:
- All core modules
- Environment variable management
- Audio recording capabilities

### langchain_agent.py
**Purpose**: LangChain-based agent orchestration

**Class**: `VoiceAgentOrchestrator`

**Key Methods**:
- `setup_tools()`: Configures LangChain tools for database operations
- `start_conversation()`: Initiates customer interaction
- `process_user_input()`: Handles user input through LangChain pipeline
- `end_conversation()`: Generates summary and updates database

**Tools Implemented**:
- `get_customer_info`: Retrieves customer data by ID
- `update_customer_info`: Updates customer records
- `add_complaint`: Records customer complaints with unique IDs
- `get_conversation_history`: Accesses conversation context

### customer_database.py
**Purpose**: Customer data management and persistence

**Key Functions**:
- `create_dummy_database()`: Generates sample customer data
- `get_random_customer()`: Selects random customer for follow-up
- `update_customer_data()`: Updates customer records with new information
- `get_customer_by_id()`: Retrieves specific customer information

**Database Schema**:
```json
{
  "customer_id": "string",
  "name": "string",
  "product(s)": ["array of strings"],
  "order_id": "string",
  "location": "string",
  "price": "number",
  "paid_status": "string",
  "payment_method": "string",
  "complain": "string",
  "complain_id": "string",
  "status": "string",
  "sentiment": "string",
  "review": "string",
  "conversation_history": ["array"]
}
```

### speech_to_text.py
**Purpose**: Audio transcription using OpenAI Whisper

**Function**: `transcribe_audio(audio_file_path, api_key)`
- Accepts WAV audio files
- Uses Whisper-1 model for transcription
- Returns transcribed text string
- Handles API errors gracefully

### text_to_speech.py
**Purpose**: Speech synthesis using ElevenLabs

**Function**: `generate_speech(text, api_key, voice_id)`
- Converts text to natural speech
- Uses eleven_multilingual_v2 model
- Default voice ID: f5HLTX707KIM4SzJYzSz
- Plays audio directly through system speakers

### audio_recorder.py
**Purpose**: Real-time audio capture and processing

**Class**: `AudioRecorder`

**Key Methods**:
- `record_audio()`: Fixed-duration recording
- `record_until_silence()`: Automatic silence detection
- Configurable sample rate and channels
- WAV file output format

### conversation_manager.py
**Purpose**: Conversation context and history management

**Class**: `ConversationManager`

**Key Methods**:
- `add_message()`: Adds speaker messages to history
- `get_history()`: Retrieves full conversation history
- `get_summary()`: Generates conversation summary with sentiment analysis

**Features**:
- Speaker identification (agent/user)
- Sentiment analysis (positive/negative/neutral)
- Complaint detection
- Summary generation

### prompt_templates.py
**Purpose**: AI prompt management and templates

**Function**: `get_support_follow_up_prompt()`
- Returns formatted prompt template
- Includes customer context placeholders
- Defines agent role and objectives
- Supports dynamic content injection

### utils.py
**Purpose**: Utility functions and helpers

**Function**: `detect_termination_intent(text)`
- Analyzes user input for conversation termination signals
- Keyword-based detection
- Returns boolean result
- Supports multiple termination phrases

## API Integration

### OpenAI Integration
**Models Used**:
- Whisper-1: Speech-to-text transcription
- GPT-4o-mini: Conversation processing and response generation

**Configuration**:
- API key via environment variable
- Error handling for rate limits and failures
- Fallback mechanisms for service unavailability

### ElevenLabs Integration
**Models Used**:
- eleven_multilingual_v2: Text-to-speech synthesis

**Configuration**:
- Voice ID: f5HLTX707KIM4SzJYzSz
- Multilingual support
- Real-time audio streaming

### LangChain Integration
**Components**:
- ChatOpenAI: LLM wrapper for GPT-4o-mini
- AgentExecutor: Tool orchestration and execution
- ConversationBufferMemory: Context management
- Custom tools: Database operations and conversation management

## Data Flow

### Conversation Initialization
1. System selects random customer from database
2. Agent generates personalized greeting
3. Conversation context is established
4. Initial message is synthesized to speech

### User Input Processing
1. Audio is captured via microphone
2. Audio is transcribed using Whisper
3. Text is processed through LangChain agent
4. Agent selects appropriate tools and generates response
5. Response is synthesized to speech
6. Conversation history is updated

### Conversation Termination
1. Termination intent is detected
2. Final summary is generated
3. Customer database is updated
4. Conversation metrics are recorded

## Error Handling

### API Failures
- OpenAI API errors: Fallback to error messages
- ElevenLabs API errors: Continue in text-only mode
- Network issues: Retry mechanisms with exponential backoff

### Audio Issues
- Microphone access denied: Fallback to text input
- Audio recording failures: Prompt for text input
- Transcription errors: Request user to repeat

### Database Errors
- File access issues: Create new database
- JSON parsing errors: Reset to default structure
- Update failures: Log errors and continue

## Performance Considerations

### Latency Optimization
- Streaming audio processing
- Concurrent API calls where possible
- Efficient conversation history management
- Optimized prompt templates

### Memory Management
- Limited conversation history retention
- Efficient JSON operations
- Garbage collection for audio buffers

### Scalability
- Stateless design for horizontal scaling
- Database abstraction for future SQL integration
- Modular architecture for component replacement

## Security Implementation

### API Key Management
- Environment variable storage
- No hardcoded credentials
- Secure key rotation support

### Data Protection
- Local data storage only
- No external data transmission except for AI processing
- Customer data anonymization options

### Input Validation
- Audio file format validation
- Text input sanitization
- API response validation

## Testing Framework

### Unit Tests
- Individual module testing
- Mock API responses
- Database operation validation

### Integration Tests
- End-to-end conversation flow
- API integration verification
- Error scenario testing

### Performance Tests
- Response time measurement
- Memory usage monitoring
- Concurrent user simulation

## Deployment Considerations

### Environment Setup
- Python 3.11+ requirement
- System dependency installation
- Audio driver configuration

### Configuration Management
- Environment-specific settings
- API key management
- Logging configuration

### Monitoring
- Conversation metrics
- API usage tracking
- Error rate monitoring
- Performance metrics

## Future Enhancements

### Planned Features
- Multi-language support
- Advanced sentiment analysis
- Integration with CRM systems
- Voice authentication
- Real-time analytics dashboard

### Technical Improvements
- Database migration to SQL
- Microservices architecture
- Container deployment
- Load balancing
- Caching layer

### AI Enhancements
- Custom model fine-tuning
- Improved conversation flow
- Predictive customer insights
- Automated escalation rules

