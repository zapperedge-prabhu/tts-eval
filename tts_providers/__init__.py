"""Factory and provider definitions for the Zapper TTS service.

Each provider implements a `synthesize` method that accepts a text
string and optional keyword parameters and returns either a tuple of
``(audio_array, sample_rate)`` or raw bytes.  The factory function
`get_provider` caches provider instances so heavy models are only
loaded once per process.  New providers should be imported and added
to the factory below.
"""

from __future__ import annotations

from typing import Dict, Optional
import os
import logging

# Import provider classes
from .bark_provider import BarkProvider
from .coqui_provider import CoquiProvider
from .elevenlabs_provider import ElevenLabsProvider
from .kokoro_provider import KokoroProvider

logger = logging.getLogger(__name__)

_providers: Dict[str, object] = {}

def get_provider(name: str):
    """Return a cached provider instance by name.

    Supported names are ``"bark"``, ``"coqui"``, ``"elevenlabs"`` and
    ``"kokoro"``.  Instances are created lazily on first use and
    cached for the lifetime of the process.

    Raises:
        ValueError: if the provider name is not recognised.
    """
    lname = name.lower()
    if lname in _providers:
        return _providers[lname]

    if lname == "bark":
        logger.info("Initializing Bark provider … this may take a while …")
        _providers[lname] = BarkProvider()
    elif lname == "coqui":
        logger.info("Initializing Coqui provider … this may take a while …")
        _providers[lname] = CoquiProvider()
    elif lname == "elevenlabs":
        logger.info("Initializing ElevenLabs provider … this may take a while …")
        # Pull credentials from environment on first load
        api_key = os.getenv("ELEVENLABS_API_KEY")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        model_id = os.getenv("ELEVENLABS_MODEL_ID")
        sample_rate = int(os.getenv("ELEVENLABS_SAMPLE_RATE", "24000"))
        _providers[lname] = ElevenLabsProvider(api_key=api_key, voice_id=voice_id, model_id=model_id, sample_rate=sample_rate)
    elif lname == "kokoro":
        logger.info("Initializing Kokoro provider … this may take a while …")
        lang_code = os.getenv("KOKORO_LANG_CODE", "a")
        voice = os.getenv("KOKORO_VOICE", "af_heart")
        _providers[lname] = KokoroProvider(lang_code=lang_code, voice=voice)
    else:
        raise ValueError(f"Unknown provider '{name}'")
    return _providers[lname]
