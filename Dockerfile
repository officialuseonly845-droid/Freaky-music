FROM python:3.10

# System tools aur FFmpeg
RUN apt-get update && apt-get install -y ffmpeg git build-essential python3-dev

WORKDIR /app
COPY . .

# Pip upgrade
RUN pip install --no-cache-dir -U pip

# Sabse pehle base libraries ek saath
RUN pip install --no-cache-dir pyrogram tgcrypto yt-dlp aiohttp python-dotenv

# Ab Pytgcalls ko bina version ke install hone do, pip khud 2.0.0+ uthayega
# Ya phir hum seedha latest stable version pakadte hain
RUN pip install --no-cache-dir pytgcalls

# Bot start karne ki command
CMD ["python", "bot.py"]
