"""Coqui TTS provider.

This provider wraps the Coqui TTS `TTS` API.  By default it uses the
English Tacotron2 model with DDC vocoder.  The provider loads the
model lazily and infers the sample rate from the synthesizer.  See
https://coqui.ai/ for more models.
"""

from __future__ import annotations

import logging
from typing import Tuple

import numpy as np

try:
    from TTS.api import TTS as CoquiTTS
except ImportError as exc:
    raise ImportError("CoquiProvider requires the 'TTS' package. Please add it to requirements.") from exc

logger = logging.getLogger(__name__)


class CoquiProvider:
    """Wrapper for the Coqui TTS engine."""

    def __init__(self, model_name: str = "tts_models/en/ljspeech/tacotron2-DDC") -> None:
        self.model_name = model_name
        self.tts = None
        self.sample_rate: int = 22050  # sensible default if model doesn't expose sample rate

    def _load(self) -> None:
        if self.tts is None:
            logger.info("Loading Coqui TTS model '%s' …", self.model_name)
            # progress_bar=False avoids printing progress to stderr
            self.tts = CoquiTTS(model_name=self.model_name, progress_bar=False)
            # Some models expose synthesizer.sample_rate, others output_sample_rate
            try:
                self.sample_rate = int(getattr(self.tts.synthesizer, "output_sample_rate", getattr(self.tts.synthesizer, "sample_rate", 22050)))
            except Exception:
                self.sample_rate = 22050
            logger.info("Coqui model loaded (sample_rate=%s)", self.sample_rate)

    def synthesize(self, text: str) -> Tuple[np.ndarray, int]:
        """Synthesize text using the Coqui engine.

        Args:
            text: The input text to synthesize.

        Returns:
            A tuple ``(audio, sample_rate)`` where ``audio`` is a 1‑D numpy
            array of float32 samples and ``sample_rate`` is the sampling rate.
        """
        if not text:
            raise ValueError("Text must not be empty for Coqui synthesis")
        self._load()
        logger.info("Generating Coqui audio …")
        # The tts() method returns a numpy array of float32 samples in [-1, 1]
        audio = self.tts.tts(text)
        return audio.astype(np.float32), self.sample_rate
