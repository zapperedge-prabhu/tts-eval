# ZapperTTSService - Replit Configuration

## Overview

ZapperTTSService is a FastAPI-based text-to-speech microservice that provides REST API endpoints for multiple TTS providers. It was originally designed to run with Docker but has been adapted to run in the Replit environment.

**Current Status:** ✅ Running on Replit (ElevenLabs provider available)

## Project Structure

```
.
├── tts_main.py              # Main FastAPI application
├── tts_providers/           # TTS provider implementations
│   ├── __init__.py         # Provider factory with conditional imports
│   ├── bark_provider.py    # Bark TTS (requires transformers, torch)
│   ├── coqui_provider.py   # Coqui TTS (requires TTS package)
│   ├── elevenlabs_provider.py  # ElevenLabs API (lightweight, available)
│   └── kokoro_provider.py  # Kokoro TTS (requires kokoro package)
├── requirements.txt         # Python dependencies
├── Dockerfile              # Original Docker configuration
└── README.md               # Original project documentation
```

## Recent Changes (Replit Adaptation)

### 2025-11-23: Updated Dependencies

1. **Dependency Management**
   - Enabled transformers and torch for Bark provider support
   - Note: These are large dependencies (~1.3GB combined) - only install on Core plan or higher
   - scipy added for audio processing support
   - ElevenLabs provider available (API-based, no local models)

2. **Import Structure**
   - Fixed relative imports in `tts_main.py` to work outside package context
   - Added conditional imports in `tts_providers/__init__.py` to gracefully handle missing dependencies
   - Providers check availability before initialization and return helpful error messages

3. **Environment Configuration**
   - Set up environment variables for ElevenLabs integration
   - Configured FastAPI to run on port 5000 (Replit's webview port)
   - Added autoscale deployment configuration

## Available Endpoints

- `GET /` or `/health` - Health check endpoint
- `POST /tts/elevenlabs` - ElevenLabs TTS (requires ELEVENLABS_API_KEY secret)
- `POST /tts/bark` - Bark TTS (not available - requires additional dependencies)
- `POST /tts/coqui` - Coqui TTS (not available - requires additional dependencies)
- `POST /tts/kokoro` - Kokoro TTS (not available - requires additional dependencies)

## Environment Variables

### Currently Configured (Shared Environment)
- `API_KEY_BARK` - API key for authenticating requests to the Bark endpoint (dev key: dev-bark-key)
- `API_KEY_COQUI` - API key for authenticating requests to the Coqui endpoint (dev key: dev-coqui-key)
- `API_KEY_ELEVENLABS` - API key for authenticating requests to the ElevenLabs endpoint (dev key: dev-elevenlabs-key-placeholder)
- `API_KEY_KOKORO` - API key for authenticating requests to the Kokoro endpoint (dev key: dev-kokoro-key)
- `ELEVENLABS_VOICE_ID` - Default voice ID for ElevenLabs
- `ELEVENLABS_MODEL_ID` - Default model ID for ElevenLabs
- `ELEVENLABS_SAMPLE_RATE` - Sample rate for audio output

### Required for Full Functionality
To use ElevenLabs TTS, you need to:
1. Get an API key from [ElevenLabs](https://elevenlabs.io/)
2. Set the `ELEVENLABS_API_KEY` secret in Replit's Secrets tab (or use the secrets pane)
3. Optionally update `API_KEY_ELEVENLABS` to a secure random value for endpoint authentication

## Usage Example

```bash
# Health check
curl http://localhost:5000/health

# Generate speech with ElevenLabs (requires valid API keys)
curl -X POST http://localhost:5000/tts/elevenlabs \
  -H "Authorization: Bearer YOUR_API_KEY_ELEVENLABS" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world from ElevenLabs!"}'
```

Response format:
```json
{
  "provider": "elevenlabs",
  "sample_rate": 24000,
  "duration_ms": 842.1,
  "audio_base64": "UklGR..."
}
```

## Enabling Additional Providers (Advanced)

To enable Bark, Coqui, or Kokoro providers:

1. **Check Storage**: Requires Core plan or higher (50GB+ storage)
2. **Update requirements.txt**: Uncomment the heavy dependencies
3. **Install**: Run `pip install -r requirements.txt`
4. **Set API Keys**: Add corresponding `API_KEY_BARK`, `API_KEY_COQUI`, `API_KEY_KOKORO` environment variables
5. **Restart**: Restart the workflow

⚠️ Warning: Installing all providers may require 2-5GB of disk space for model downloads.

## Deployment

The service is configured for autoscale deployment:
- Automatically scales based on incoming requests
- Suitable for stateless TTS API
- Configure secrets before deploying to production

## Troubleshooting

### Provider Not Available Error
If you get "provider is not available" errors, the required Python packages are not installed. Check the error message for which packages to install.

### Disk Quota Exceeded
If you run out of space when installing dependencies, you're on a Starter plan (2GB limit). Either:
- Use only the lightweight ElevenLabs provider (current setup)
- Upgrade to Core plan (50GB storage)
- Deploy to a different platform with more storage

### Authorization Errors
Make sure you've set the correct API keys:
- `API_KEY_ELEVENLABS` - for authenticating incoming requests
- `ELEVENLABS_API_KEY` - for calling ElevenLabs API (get from elevenlabs.io)

## Architecture Notes

This is a microservice designed to complement the ZapperSensitiveInfoDetector project. It follows similar patterns:
- Bearer token authentication for each endpoint
- Detailed request/response logging
- Base64-encoded WAV audio output
- Extensible provider architecture

## User Preferences

None specified yet.
