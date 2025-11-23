"""Package entry for the Zapper TTS microservice.

This package exposes the FastAPI app via the `tts_main` module.  It
also makes provider classes available for import from the
`tts_providers` subpackage.
"""

from .tts_main import app  # noqa: F401
