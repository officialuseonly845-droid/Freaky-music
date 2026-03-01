import os
import asyncio
import logging
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
from aiohttp import web
import yt_dlp

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

API_ID         = int(os.getenv("API_ID", "0"))
API_HASH       = os.getenv("API_HASH", "")
BOT_TOKEN      = os.getenv("BOT_TOKEN", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

bot       = Client("VideoBot",  api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
assistant = Client("Assistant", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call_py   = PyTgCalls(assistant)

@bot.on_message(filters.all)
async def debug_all(_, message):
    logger.info(f"📨 Message received: {message.text} from {message.from_user.id if message.from_user else 'unknown'} in chat {message.chat.id}")

@bot.on_message(filters.command("start"))
async def start_handler(_, message):
    logger.info("✅ Start command received!")
    await message.reply("👋 Bot is working!")

@bot.on_message(filters.command("play"))
async def play_handler(_, message):
    logger.info(f"🎬 Play command received: {message.text}")
    try:
        if len(message.command) < 2:
            return await message.reply("❌ Usage: `/play <YouTube link>`")

        url = message.text.split(None, 1)[1].strip()
        m = await message.reply("⏳ Processing...")

        ydl_opts = {
            "format": "best[height<=480][ext=mp4]/best[ext=mp4]/best",
            "quiet": True,
            "noplaylist": True,
            "no_warnings": True,
            "cookiefile": COOKIES_FILE,
        }

        await m.edit("🔗 Fetching stream URL...")
        loop = asyncio.get_event_loop()

        def fetch():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info["url"], info.get("title", "Unknown")

        stream_url, title = await loop.run_in_executor(None, fetch)
        logger.info(f"✅ Stream URL fetched for: {title}")

        await m.edit("📡 Joining voice chat...")
        await call_py.play(
            message.chat.id,
            MediaStream(
                stream_url,
                audio_quality=AudioQuality.HIGH,
                video_quality=VideoQuality.SD_480p,
            )
        )
        await m.edit(f"🎬 **Playing:** `{title}`\n\n⏸ /pause | ▶️ /resume | ⏹ /stop")

    except Exception as e:
        logger.error(f"❌ Play error: {e}", exc_info=True)
        await message.reply(f"❌ Error: `{e}`")

@bot.on_message(filters.command("pause"))
async def pause_handler(_, message):
    try:
        await call_py.pause_stream(message.chat.id)
        await message.reply("⏸ Paused.")
    except Exception as e:
        await message.reply(f"❌ {e}")

@bot.on_message(filters.command("resume"))
async def resume_handler(_, message):
    try:
        await call_py.resume_stream(message.chat.id)
        await message.reply("▶️ Resumed.")
    except Exception as e:
        await message.reply(f"❌ {e}")

@bot.on_message(filters.command("stop"))
async def stop_handler(_, message):
    try:
        await call_py.leave_call(message.chat.id)
        await message.reply("⏹ Stopped.")
    except Exception as e:
        await message.reply(f"❌ {e}")

async def health_check(request):
    return web.Response(text="✅ Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"✅ HTTP server on port {port}")

async def main():
    try:
        await bot.start()
        logger.info("✅ Bot started")
        await assistant.start()
        logger.info("✅ Assistant started")
        await call_py.start()
        logger.info("✅ PyTgCalls started")
        await start_web_server()
        logger.info("🚀 All online!")
        await idle()
    except Exception as e:
        logger.critical(f"❌ Fatal: {e}", exc_info=True)
        raise SystemExit(1)
    finally:
        try:
            await bot.stop()
            await assistant.stop()
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())
