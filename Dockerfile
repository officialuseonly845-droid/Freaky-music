FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -U pip

RUN pip install --no-cache-dir \
    pyrogram \
    tgcrypto \
    yt-dlp \
    aiohttp \
    python-dotenv

RUN pip install --no-cache-dir ntgcalls

RUN pip install --no-cache-dir --pre --no-deps pytgcalls

ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1

CMD ["python", "-u", "bot.py"]
