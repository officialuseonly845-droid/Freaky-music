# Slim ki jagah full image use kar rahe hain taaki dependency conflict na ho
FROM python:3.10

# System updates aur FFmpeg
RUN apt-get update && apt-get install -y ffmpeg git

WORKDIR /app
COPY . .

# Sabse pehle pip upgrade
RUN pip install --no-cache-dir -U pip

# Sabse stable libraries ka combination
RUN pip install --no-cache-dir pyrogram tgcrypto yt-dlp aiohttp python-dotenv
RUN pip install --no-cache-dir pytgcalls==2.0.0.dev24

# Bot start command
CMD ["python", "bot.py"]
