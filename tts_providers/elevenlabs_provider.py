"""ElevenLabs TTS provider.

This provider wraps the official ElevenLabs Python SDK.  It
synthesizes speech via ElevenLabs' hosted API.  An API key is
required and should be provided either in the environment variable
`ELEVENLABS_API_KEY` or passed to the constructor.  Optional
defaults for ``voice_id``, ``model_id`` and ``sample_rate`` can be
configured via environment variables or constructor arguments.

The `synthesize` method returns raw audio bytes (already encoded as
PCM).  If a sample rate is provided, the caller can package it into a
WAV.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

try:
    from elevenlabs.client import ElevenLabs
except ImportError as exc:
    raise ImportError("ElevenLabsProvider requires the 'elevenlabs' package. Please add it to requirements.") from exc

logger = logging.getLogger(__name__)


class ElevenLabsProvider:
    """Wrapper around the ElevenLabs API client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        sample_rate: int = 24000,
    ) -> None:
        if not api_key:
            logger.warning("ElevenLabsProvider initialized without an API key; calls will fail.")
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.sample_rate = sample_rate
        self.client: Optional[ElevenLabs] = None

    def _load(self) -> None:
        if self.client is None:
            logger.info("Creating ElevenLabs client …")
            # When no API key is provided, the client will throw on first call
            self.client = ElevenLabs(api_key=self.api_key)

    def synthesize(self, text: str, voice_id: Optional[str] = None, model_id: Optional[str] = None) -> Tuple[bytes, int]:
        """Generate speech using ElevenLabs.

        Args:
            text: Text to be synthesized.
            voice_id: Optional voice ID overriding the default.
            model_id: Optional model ID overriding the default.

        Returns:
            A tuple ``(audio_bytes, sample_rate)``.  ``audio_bytes``
            contains the raw PCM stream returned by ElevenLabs and
            ``sample_rate`` is the configured sampling rate.
        """
        if not text:
            raise ValueError("Text must not be empty for ElevenLabs synthesis")
        self._load()
        use_voice_id = voice_id or self.voice_id
        use_model_id = model_id or self.model_id
        if not use_voice_id or not use_model_id:
            logger.warning("Voice ID or model ID is missing; using ElevenLabs defaults")
        logger.info("Requesting ElevenLabs synthesis (voice_id=%s, model_id=%s)", use_voice_id, use_model_id)
        # The SDK returns a generator yielding chunks of audio bytes
        audio_stream = self.client.text_to_speech.stream(
            text=text,
            voice_id=use_voice_id,
            model_id=use_model_id,
        )
        # Concatenate all bytes into one blob
        audio_bytes = b"".join(audio_stream)
        return audio_bytes, self.sample_rate
