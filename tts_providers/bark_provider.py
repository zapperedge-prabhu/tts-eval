"""Bark TTS provider.

This provider wraps the `suno/bark-small` model available from
HuggingFace's `transformers` library.  The model and processor are
loaded on first use and then reused for subsequent requests.  To
change the voice preset or model, pass different values to the
``synthesize`` method.

Example:
    from tts_providers.bark_provider import BarkProvider
    provider = BarkProvider()
    audio, sample_rate = provider.synthesize("Hello world")
"""

from __future__ import annotations

import logging
from typing import Tuple, Optional

import numpy as np

try:
    from transformers import BarkModel, BarkProcessor
except ImportError as exc:
    raise ImportError("BarkProvider requires the 'transformers' package. Please add it to requirements.") from exc

logger = logging.getLogger(__name__)


class BarkProvider:
    """Wrapper around the Bark small model.

    The provider lazily loads the model and processor on the first call
    to :meth:`synthesize`.  Subsequent calls reuse the loaded model.
    """

    def __init__(self, model_name: str = "suno/bark-small") -> None:
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.sample_rate: Optional[int] = None

    def _load(self) -> None:
        """Load the Bark model and processor if not already loaded."""
        if self.model is None or self.processor is None:
            logger.info("Loading Bark model '%s' …", self.model_name)
            self.model = BarkModel.from_pretrained(self.model_name)
            self.processor = BarkProcessor.from_pretrained(self.model_name)
            # Determine the sampling rate from the generation config
            self.sample_rate = self.model.generation_config.sample_rate
            logger.info("Bark model loaded (sample_rate=%s)", self.sample_rate)

    def synthesize(self, text: str, voice_preset: Optional[str] = None) -> Tuple[np.ndarray, int]:
        """Synthesize text into speech.

        Args:
            text: The input text to synthesize.
            voice_preset: Optional voice preset supported by Bark.

        Returns:
            A tuple ``(audio, sample_rate)`` where ``audio`` is a 1‑D numpy
            array of float32 samples in the range [-1, 1] and ``sample_rate``
            is the sampling rate in Hz.
        """
        if not text:
            raise ValueError("Text must not be empty for Bark synthesis")
        self._load()
        preset = voice_preset or "v2/en_speaker_2"
        logger.info("Generating Bark audio with preset '%s'", preset)
        inputs = self.processor(text, voice_preset=preset)
        # Generate returns a list with one element per input
        speech_output = self.model.generate(**inputs)
        # Convert to numpy on CPU
        audio = speech_output.cpu().numpy()[0]
        return audio.astype(np.float32), self.sample_rate
