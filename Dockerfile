FROM python:3.10-slim

# System dependencies aur FFmpeg install karein
RUN apt-get update && apt-get install -y ffmpeg python3-pip git

WORKDIR /app
COPY . .

# Sabhi libraries ko ek saath install karein taaki dependency conflict na ho
RUN pip install --no-cache-dir -U pip
RUN pip install --no-cache-dir pyrogram tgcrypto yt-dlp aiohttp python-dotenv pytgcalls

# Bot start karne ki command
CMD ["python", "bot.py"]
