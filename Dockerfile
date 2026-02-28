FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -U pip

# Step 1: pyrofork pehle install karo (pyrogram ka compatible fork)
RUN pip install --no-cache-dir pyrofork tgcrypto

# Step 2: baaki dependencies
RUN pip install --no-cache-dir yt-dlp aiohttp python-dotenv

# Step 3: py-tgcalls â€” ab pyrofork already present hai to sahi pick karega
RUN pip install --no-cache-dir py-tgcalls

ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1

CMD ["python", "-u", "bot.py"]
