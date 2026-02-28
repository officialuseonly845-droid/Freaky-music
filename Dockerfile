FROM python:3.10-slim

# System tools install karein jo 'tgcalls' build karne ke liye chahiye
RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3-pip \
    git \
    build-essential \
    python3-dev

WORKDIR /app
COPY . .

# Pip upgrade karein
RUN pip install --no-cache-dir -U pip

# Sabse pehle base libraries
RUN pip install --no-cache-dir pyrogram tgcrypto yt-dlp aiohttp python-dotenv

# Ab pytgcalls install karein (Version 2.0.0.dev24 ya latest stable)
# Hum 'wayla' extra use karenge jo modern streaming ke liye hai
RUN pip install --no-cache-dir pytgcalls==2.0.0.dev24

# Bot start karne ki command
CMD ["python", "bot.py"]
