FROM python:3.10-slim

# Install system dependencies (FFmpeg is mandatory for video)
RUN apt-get update && apt-get install -y ffmpeg python3-pip

WORKDIR /app
COPY . .

# Install Python libraries directly
RUN pip install pyrogram pytgcalls[wayla] yt-dlp aiohttp python-dotenv

# Command to run the bot
CMD ["python", "bot.py"]
