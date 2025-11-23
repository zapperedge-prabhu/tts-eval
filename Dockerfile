FROM python:3.11-slim

# Create and set working directory
WORKDIR /app

# Install system dependencies.  The Kokoro TTS provider uses espeak-ng for
# fallback grapheme‑to‑phoneme conversion.  libsndfile1 is required by
# some audio libraries.  libgl1 is kept to satisfy dependencies of
# certain neural models.  We deliberately omit heavy image processing
# packages used in the SensitiveInfoDetector (e.g. tesseract).
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libgl1 \
    espeak-ng \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set default port.  Azure App Service will override this environment
# variable.
ENV PORT=8000

# Default command uses uvicorn to serve the FastAPI app
CMD ["sh", "-c", "uvicorn tts_main:app --host 0.0.0.0 --port ${PORT:-8000}"]