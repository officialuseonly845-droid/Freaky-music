FROM python:3.10-slim

# System tools aur FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Pip upgrade
RUN pip install --no-cache-dir -U pip

# Base libraries
RUN pip install --no-cache-dir \
    pyrogram \
    tgcrypto \
    yt-dlp \
    aiohttp \
    python-dotenv

# pytgcalls 3.x+ mein tgcalls dependency nahi hai
RUN pip install --no-cache-dir "pytgcalls>=3.0.0"

CMD ["python", "bot.py"]
