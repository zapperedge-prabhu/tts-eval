"""Main entry point for the Zapper TTS microservice.

This FastAPI application exposes endpoints for synthesising speech
using several text‑to‑speech providers.  Each endpoint is protected
with a bearer token (API key) and returns base64 encoded WAV audio
along with basic metadata.  The design mirrors that of the existing
ZapperSensitiveInfoDetector so that both services can be deployed and
managed in a similar way.
"""

from __future__ import annotations

import base64
import io
import os
import time
import wave
from typing import Any, Dict

import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import logging

from .tts_providers import get_provider


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info("=== Incoming Request ===")
    logger.info("Method: %s", request.method)
    logger.info("URL: %s", request.url)
    logger.info("Client: %s", request.client.host if request.client else 'Unknown')
    logger.info("Headers: %s", dict(request.headers))
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info("=== Response ===")
    logger.info("Status: %s", response.status_code)
    logger.info("Process Time: %.3fs", process_time)
    logger.info("=====================")
    return response


@app.get("/")
@app.get("/health")
async def health_check():
    """Simple health check to verify the service is running."""
    return {"status": "healthy", "service": "ZapperTTSService"}


def validate_key(request: Request, key_env: str) -> None:
    """Validate the Authorization header against an environment variable.

    This helper behaves similarly to the one in the SensitiveInfoDetector.  If
    the header is missing, malformed or does not match the configured key
    the appropriate HTTPException is raised.
    """
    logger.info("Validating API key for environment variable: %s", key_env)
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        logger.warning("Missing or invalid Authorization header format")
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = auth.split(" ", 1)[1]
    expected = os.getenv(key_env)
    if expected is None or expected == "":
        logger.error("Environment variable %s is not set!", key_env)
        raise HTTPException(status_code=500, detail=f"Server configuration error: {key_env} not configured")
    if token != expected:
        logger.warning("Invalid API key provided for %s", key_env)
        raise HTTPException(status_code=403, detail="Invalid API key")
    logger.info("API key validated successfully for %s", key_env)


def audio_to_base64(audio: Any, sample_rate: int) -> str:
    """Convert either a numpy array or raw bytes into a base64 WAV string.

    If ``audio`` is already bytes, it is assumed to be a complete audio
    stream at the correct sample rate (e.g. from ElevenLabs) and is
    simply encoded.  Otherwise the numpy array is normalised and
    written into an in-memory WAV container.

    Args:
        audio: numpy array of floats in [-1, 1] or raw PCM bytes
        sample_rate: the sample rate of the audio

    Returns:
        A base64 encoded WAV file.
    """
    # If it's already bytes we simply base64 encode directly
    if isinstance(audio, (bytes, bytearray)):
        logger.debug("Audio is raw bytes; encoding directly to base64")
        return base64.b64encode(audio).decode('utf-8')
    # Otherwise we assume a 1-D numpy array
    if not isinstance(audio, np.ndarray):
        raise ValueError("Audio must be either numpy.ndarray or bytes")
    audio_arr = audio.astype(np.float32)
    # Normalise to the range [-1, 1] if necessary
    max_abs = np.max(np.abs(audio_arr)) if audio_arr.size else 0.0
    if max_abs > 1.0:
        audio_arr = audio_arr / max_abs
    # Convert to 16-bit PCM
    int16_audio = (audio_arr * 32767.0).astype(np.int16)
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 2 bytes per sample
        wf.setframerate(sample_rate)
        wf.writeframes(int16_audio.tobytes())
    wav_bytes = buffer.getvalue()
    return base64.b64encode(wav_bytes).decode('utf-8')


@app.post("/tts/bark")
async def tts_bark(req: Request) -> JSONResponse:
    """Synthesize speech using the Bark model."""
    validate_key(req, "API_KEY_BARK")
    data = await req.json()
    text = data.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' in request body")
    voice_preset = data.get("voice_preset")
    provider = get_provider("bark")
    start = time.time()
    try:
        audio, sample_rate = provider.synthesize(text, voice_preset=voice_preset)
    except Exception as exc:
        logger.exception("Bark synthesis failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Bark synthesis failed: {exc}")
    duration_ms = (time.time() - start) * 1000.0
    b64_audio = audio_to_base64(audio, sample_rate)
    return JSONResponse({
        "provider": "bark",
        "sample_rate": sample_rate,
        "duration_ms": duration_ms,
        "audio_base64": b64_audio,
    })


@app.post("/tts/coqui")
async def tts_coqui(req: Request) -> JSONResponse:
    """Synthesize speech using the Coqui TTS model."""
    validate_key(req, "API_KEY_COQUI")
    data = await req.json()
    text = data.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' in request body")
    provider = get_provider("coqui")
    start = time.time()
    try:
        audio, sample_rate = provider.synthesize(text)
    except Exception as exc:
        logger.exception("Coqui synthesis failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Coqui synthesis failed: {exc}")
    duration_ms = (time.time() - start) * 1000.0
    b64_audio = audio_to_base64(audio, sample_rate)
    return JSONResponse({
        "provider": "coqui",
        "sample_rate": sample_rate,
        "duration_ms": duration_ms,
        "audio_base64": b64_audio,
    })


@app.post("/tts/elevenlabs")
async def tts_elevenlabs(req: Request) -> JSONResponse:
    """Synthesize speech using the ElevenLabs hosted API."""
    validate_key(req, "API_KEY_ELEVENLABS")
    data = await req.json()
    text = data.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' in request body")
    voice_id = data.get("voice_id")
    model_id = data.get("model_id")
    provider = get_provider("elevenlabs")
    # If the provider was initialised without an API key, this call will fail
    start = time.time()
    try:
        audio_bytes, sample_rate = provider.synthesize(text, voice_id=voice_id, model_id=model_id)
    except Exception as exc:
        logger.exception("ElevenLabs synthesis failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"ElevenLabs synthesis failed: {exc}")
    duration_ms = (time.time() - start) * 1000.0
    b64_audio = audio_to_base64(audio_bytes, sample_rate)
    return JSONResponse({
        "provider": "elevenlabs",
        "sample_rate": sample_rate,
        "duration_ms": duration_ms,
        "audio_base64": b64_audio,
    })


@app.post("/tts/kokoro")
async def tts_kokoro(req: Request) -> JSONResponse:
    """Synthesize speech using the Kokoro model."""
    validate_key(req, "API_KEY_KOKORO")
    data = await req.json()
    text = data.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' in request body")
    # Optional overrides for language and voice
    voice = data.get("voice")
    lang_code = data.get("lang_code")
    provider = get_provider("kokoro")
    start = time.time()
    try:
        audio, sample_rate = provider.synthesize(text, voice=voice, lang_code=lang_code)
    except Exception as exc:
        logger.exception("Kokoro synthesis failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Kokoro synthesis failed: {exc}")
    duration_ms = (time.time() - start) * 1000.0
    b64_audio = audio_to_base64(audio, sample_rate)
    return JSONResponse({
        "provider": "kokoro",
        "sample_rate": sample_rate,
        "duration_ms": duration_ms,
        "audio_base64": b64_audio,
    })
