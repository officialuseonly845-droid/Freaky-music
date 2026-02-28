FROM python:3.10-slim

# System dependencies aur FFmpeg install karein
RUN apt-get update && apt-get install -y ffmpeg python3-pip git

WORKDIR /app
COPY . .

# Pehle pip ko upgrade karein phir compatible libraries install karein
RUN pip install --no-cache-dir -U pip
RUN pip install --no-cache-dir pyrogram tgcrypto yt-dlp aiohttp python-dotenv
RUN pip install --no-cache-dir pytgcalls==0.9.10

# Bot start karne ki command
CMD ["python", "bot.py"]
