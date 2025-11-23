"""Kokoro TTS provider.

Kokoro is an 82M parameter open‑weight TTS model supporting multiple
languages.  This provider wraps the `KPipeline` from the `kokoro`
package.  It collects all the streaming chunks into a single numpy
array and returns the audio along with the sample rate (24 kHz).
"""

from __future__ import annotations

import logging
from typing import Tuple, Optional

import numpy as np

try:
    from kokoro import KPipeline
except ImportError as exc:
    raise ImportError("KokoroProvider requires the 'kokoro' package. Please add it to requirements.") from exc

logger = logging.getLogger(__name__)


class KokoroProvider:
    """Wrapper for the Kokoro TTS pipeline."""

    def __init__(self, lang_code: str = "a", voice: str = "af_heart") -> None:
        self.lang_code = lang_code
        self.voice = voice
        self.pipeline: Optional[KPipeline] = None
        # Kokoro outputs 24 kHz audio by default
        self.sample_rate: int = 24000

    def _load(self) -> None:
        if self.pipeline is None:
            logger.info("Initializing Kokoro pipeline (lang_code=%s) …", self.lang_code)
            self.pipeline = KPipeline(lang_code=self.lang_code)
            logger.info("Kokoro pipeline loaded")

    def synthesize(self, text: str, voice: Optional[str] = None, lang_code: Optional[str] = None) -> Tuple[np.ndarray, int]:
        """Generate speech using Kokoro.

        Args:
            text: Text to synthesize.
            voice: Optional voice name overriding the default.
            lang_code: Optional language code overriding the default.

        Returns:
            A tuple ``(audio, sample_rate)`` where ``audio`` is a 1‑D
            numpy array of float32 samples.
        """
        if not text:
            raise ValueError("Text must not be empty for Kokoro synthesis")
        # If lang_code overrides, reload the pipeline for new language
        if lang_code and lang_code != self.lang_code:
            self.lang_code = lang_code
            self.pipeline = None
        self._load()
        use_voice = voice or self.voice
        logger.info("Generating Kokoro audio (lang_code=%s, voice=%s) …", self.lang_code, use_voice)
        # Kokoro returns a generator yielding (generation_status, phoneme_status, audio_chunk)
        audio_chunks = []
        for _, _, audio in self.pipeline(text, voice=use_voice):
            # Each audio chunk is a torch.Tensor; convert to numpy
            try:
                audio_chunks.append(audio.numpy())
            except Exception:
                # If already numpy
                audio_chunks.append(np.asarray(audio))
        if audio_chunks:
            audio_out = np.concatenate(audio_chunks).astype(np.float32)
        else:
            audio_out = np.array([], dtype=np.float32)
        return audio_out, self.sample_rate
