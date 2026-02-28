FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -U pip

# Step 1: Base libraries
RUN pip install --no-cache-dir \
    pyrogram \
    tgcrypto \
    yt-dlp \
    aiohttp \
    python-dotenv

# Step 2: ntgcalls alag install karo
RUN pip install --no-cache-dir ntgcalls

# Step 3: pytgcalls dev version, --no-deps zaroori hai
RUN pip install --no-cache-dir --pre --no-deps pytgcalls

ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1

CMD ["python", "-u", "bot.py"]
