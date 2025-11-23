# 🎤 ZapperTTSService

The **ZapperTTSService** is a companion microservice to the existing
`ZapperSensitiveInfoDetector`.  It exposes a simple REST API to
synthesize speech from text using a variety of open‑source and hosted
text‑to‑speech (TTS) providers.  This service is intended for
benchmarking and comparing the quality and latency of different TTS
models.  New providers can be added by dropping a new provider class
into `tts_service/tts_providers` and wiring an endpoint.

## 🚀 Features

* ✅ Four built‑in TTS providers:
  * **Bark** — lightweight transformer model from Suno hosted on
    HuggingFace
  * **Coqui TTS** — open source Tacotron2+DDC model
  * **ElevenLabs** — hosted API with multiple voices and models
  * **Kokoro** — open weight 82M parameter model with multiple
    voices
* ✅ FastAPI based API with bearer token authentication per provider
* ✅ Returns both WAV audio (base64 encoded) and basic timing metrics
* ✅ Easily extensible by adding new provider classes
* ✅ Docker container ready for Azure App Service deployment

## 📦 Quick Start

### Prerequisites

* Docker installed on your machine
* Optional: valid ElevenLabs API key for the ElevenLabs endpoint

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ZapperTTSService.git
cd ZapperTTSService/tts_service
```

### 2. Configure Environment Variables

Copy the example environment file and fill in the API keys:

```bash
cp .env.example .env

# Generate secure API keys for each endpoint
openssl rand -base64 32  # repeat four times

# Edit .env and replace the placeholders
nano .env
```

The following variables are required:

```env
# API keys used to authenticate incoming requests on each endpoint
API_KEY_BARK=<your-secure-token>
API_KEY_COQUI=<your-secure-token>
API_KEY_ELEVENLABS=<your-secure-token>
API_KEY_KOKORO=<your-secure-token>

# ElevenLabs credentials (only required if you intend to use ElevenLabs)
ELEVENLABS_API_KEY=<your-elevenlabs-api-key>
ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb
ELEVENLABS_MODEL_ID=eleven_flash_v2_5
ELEVENLABS_SAMPLE_RATE=24000

# Kokoro defaults
KOKORO_LANG_CODE=a        # a = US English, b = British, etc.
KOKORO_VOICE=af_heart
```

### 3. Build the Docker Image

```bash
docker build -t zapper-tts:latest .
```

### 4. Run the Container

```bash
docker run -d \
  --name zapper-tts \
  --env-file .env \
  -p 8000:8000 \
  zapper-tts:latest

docker logs -f zapper-tts  # follow logs
```

### 5. Test the Service

Each endpoint requires the appropriate bearer token.  Here is an example
using `curl` for the Bark provider:

```bash
curl -X POST http://localhost:8000/tts/bark \
  -H "Authorization: Bearer $API_KEY_BARK" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world from Bark!"}'

# The response will contain a base64‑encoded WAV in the `audio_base64`
# field.  You can decode and save it to listen locally:
#   echo "<base64>" | base64 -d > output.wav && aplay output.wav
```

The response JSON has the following structure:

```json
{
  "provider": "bark",
  "sample_rate": 24000,
  "duration_ms": 842.1,
  "audio_base64": "UklGR..."
}
```

### API Endpoints

| Method | Path            | Description                                   |
|-------:|----------------|-------------------------------------------------|
|  `GET` | `/` or `/health` | Returns service health status                 |
|  `POST`| `/tts/bark`     | Synthesize speech using Bark                  |
|  `POST`| `/tts/coqui`    | Synthesize speech using Coqui TTS             |
|  `POST`| `/tts/elevenlabs`| Synthesize speech using ElevenLabs (requires
  `ELEVENLABS_API_KEY`)                                      |
|  `POST`| `/tts/kokoro`   | Synthesize speech using Kokoro                |

Each `POST` endpoint accepts a JSON body with at least a `text` field.
Additional optional parameters are listed below:

* **Bark**: `voice_preset` — one of the presets supported by the
  `BarkProcessor` (defaults to `v2/en_speaker_2`).
* **Coqui**: no additional parameters at the moment.  Change the
  model by editing the provider class.
* **ElevenLabs**: `voice_id` and `model_id` override the default
  environment variables.  If omitted, the values from the `.env`
  file are used.
* **Kokoro**: `voice` selects one of the available Kokoro voices;
  `lang_code` overrides the default language code.

### Response Format

Successful responses return HTTP 200 and contain:

* `provider` – which TTS provider was used
* `sample_rate` – the sampling rate of the generated audio
* `duration_ms` – how long the synthesis took on the server
* `audio_base64` – base64 encoded WAV audio

Error responses use standard HTTP status codes (400 for bad requests,
401 for missing Authorization header, 403 for invalid token, 500 for
server errors) and return a JSON body with a `detail` field.

## 🧩 Adding New Providers

To add support for another TTS service, create a new class in
`tts_providers/your_provider.py` implementing a `synthesize(text,
**kwargs)` method that returns a `(numpy.ndarray audio, int
sample_rate)` or `bytes` and then wire it into the `get_provider`
function in `tts_main.py`.  Add a new endpoint similar to the
existing ones and assign a new `API_KEY_*` environment variable.

## 📜 License

This project is released under the MIT License.  See the root
`LICENSE` file for details.