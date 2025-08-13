# AI Voice Agent Setup Guide

This guide provides step-by-step instructions for setting up and running the AI Voice Agent for Support Follow-Up.

## Prerequisites

### System Requirements
- **Operating System**: Ubuntu 22.04 or later (Linux recommended)
- **Python**: Version 3.11 or higher
- **Memory**: At least 4GB RAM
- **Storage**: 2GB free space for dependencies
- **Audio**: Microphone and speakers (for voice mode)

### API Keys Required
1. **OpenAI API Key** (Required)
   - Sign up at https://platform.openai.com/
   - Create an API key in your dashboard
   - Ensure you have credits available

2. **ElevenLabs API Key** (Optional)
   - Sign up at https://elevenlabs.io/
   - Get your API key from the profile section
   - Required only for speech synthesis (text mode works without it)

## Installation Steps

### Step 1: System Dependencies
Install required system packages:

```bash
# Update package list
sudo apt-get update

# Install build tools and audio libraries
sudo apt-get install -y build-essential portaudio19-dev python3-dev python3.11-dev

# Install additional audio dependencies (optional)
sudo apt-get install -y libasound2-dev
```

### Step 2: Python Environment
Ensure you're using Python 3.11:

```bash
# Check Python version
python3 --version

# If needed, install Python 3.11
sudo apt-get install -y python3.11 python3.11-dev python3.11-venv
```

### Step 3: Project Setup
Navigate to the project directory and install dependencies:

```bash
# Navigate to the AI Voice Agent directory
cd ai_voice_agent

# Install Python dependencies
pip install -r requirements.txt
```

If you encounter issues with PyAudio, try:
```bash
# Install PyAudio separately
pip install pyaudio

# If that fails, try with system package
sudo apt-get install python3-pyaudio
```

### Step 4: API Key Configuration
Configure your API keys in the `.env` file:

```bash
# Edit the .env file
nano .env
```

Add your API keys:
```
OPENAI_API_KEY=sk-your-actual-openai-key-here
ELEVENLABS_API_KEY=your-actual-elevenlabs-key-here
```

**Important**: Replace the placeholder values with your actual API keys.

### Step 5: Verify Installation
Run the test script to verify everything is working:

```bash
python3 test_basic_functionality.py
```

Expected output should show most tests passing. If ElevenLabs API key is not configured, one test may fail, but the system will still work in text mode.

## Running the Agent

### Option 1: Text-Only Mode (Recommended for Testing)
```bash
python3 demo_text_mode.py
```

This mode:
- Doesn't require audio hardware
- Works without ElevenLabs API key
- Perfect for testing core functionality
- Uses text input/output only

### Option 2: Full Voice Mode
```bash
python3 main.py
```

This mode:
- Requires microphone and speakers
- Needs both OpenAI and ElevenLabs API keys
- Provides complete speech-to-speech experience
- Select option "1" for text input or "2" for voice input

## Troubleshooting

### Common Installation Issues

#### PyAudio Installation Fails
```bash
# Install system dependencies first
sudo apt-get install portaudio19-dev python3.11-dev

# Then try installing PyAudio
pip install pyaudio
```

#### Permission Denied for Audio
```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Log out and log back in, or restart
```

#### API Key Not Working
1. Verify the key is correct in `.env`
2. Check if you have API credits
3. Ensure no extra spaces in the `.env` file
4. Try regenerating the API key

#### Import Errors
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Testing Individual Components

#### Test Customer Database
```python
python3 -c "from customer_database import get_random_customer; print(get_random_customer())"
```

#### Test OpenAI Connection
```python
python3 -c "from langchain_agent import VoiceAgentOrchestrator; import os; from dotenv import load_dotenv; load_dotenv(); agent = VoiceAgentOrchestrator(os.getenv('OPENAI_API_KEY')); print('OpenAI connection successful')"
```

## Configuration Options

### Customizing the Company
Edit `prompt_templates.py` to change company information:
```python
# Change "RichDaddy Incorporation" to your company name
# Modify the agent's role and responsibilities
```

### Changing Voice Settings
Edit `text_to_speech.py` to modify voice parameters:
```python
# Change voice_id to use different ElevenLabs voices
# Modify model to use different TTS models
```

### Adding More Customers
Edit `customer_database.py` to add more sample customers:
```python
# Add new customer records to the customers list
# Include all required fields for each customer
```

## Performance Optimization

### For Better Audio Quality
- Use a good quality microphone
- Ensure quiet environment
- Adjust silence detection thresholds in `audio_recorder.py`

### For Faster Response Times
- Use faster OpenAI models (though GPT-4o-mini is already optimized)
- Reduce conversation history length
- Optimize prompt templates

### For Lower Costs
- Use text mode for development and testing
- Implement conversation length limits
- Cache common responses

## Security Considerations

### API Key Security
- Never commit `.env` file to version control
- Use environment variables in production
- Rotate API keys regularly
- Monitor API usage

### Data Privacy
- Customer data is stored locally in JSON format
- No data is sent to external services except for AI processing
- Consider encryption for sensitive customer information

## Next Steps

After successful setup:
1. Test with the demo script
2. Customize for your specific use case
3. Add real customer data
4. Deploy to production environment
5. Monitor and optimize performance

For additional support, refer to the main README.md file or check the troubleshooting section.

