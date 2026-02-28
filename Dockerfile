FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -U pip

# Exact pinned versions — YukkiMusicBot production stack
RUN pip install --no-cache-dir \
    "pyrogram==2.0.106" \
    "TgCrypto==1.2.5" \
    "py-tgcalls==0.9.5" \
    "yt-dlp" \
    "aiohttp" \
    "python-dotenv"

ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1

CMD ["python", "-u", "bot.py"]
