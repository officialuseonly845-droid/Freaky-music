import os
import shutil
import asyncio
import logging
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
import yt_dlp
from aiohttp import web

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- CONFIG ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")

bot = Client("VideoBot", API_ID, API_HASH, bot_token=BOT_TOKEN)
assistant = Client("Assistant", API_ID, API_HASH, session_string=SESSION_STRING)
call_py = PyTgCalls(assistant)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- GLOBAL ERROR HANDLER ---
# Ye function kisi bhi unhandled error ko pakad lega aur bot ko band hone se bachayega
@bot.on_message(group=-1) # Group -1 matlab ye har message par check karega
async def error_resolver(client, message):
    try:
        await message.continue_propagation() # Normal commands ko chalne do
    except Exception as e:
        logger.error(f"Global Error Caught: {e}")
        # Agar bada error hai toh user ko bata do, warna silent raho
        if "Message not found" not in str(e):
            await message.reply(f"⚠️ **Ek Error Aaya Hai:** `{e}`\nBot abhi bhi online hai.")

# --- UPTIME SERVER ---
async def health_check(request):
    return web.Response(text="Bot is Alive & Error Protected!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()

# --- HELPERS ---
async def join_assistant(chat_id):
    try:
        await assistant.get_chat_member(chat_id, "me")
        return True
    except Exception:
        try:
            invite_link = await bot.export_chat_invite_link(chat_id)
            await assistant.join_chat(invite_link)
            return True
        except Exception as e:
            logger.error(f"Assistant Join Error: {e}")
            return f"❌ Assistant join nahi kar paya: {e}"

def clear_downloads():
    if os.path.exists(DOWNLOAD_DIR):
        try:
            shutil.rmtree(DOWNLOAD_DIR)
            os.makedirs(DOWNLOAD_DIR)
        except: pass

# --- COMMANDS (Wrapped in Try-Except) ---

@bot.on_message(filters.command("play") & filters.group)
async def play_handler(_, message):
    try:
        if len(message.command) < 2:
            return await message.reply("❌ Usage: `/play <link>`")
        
        url = message.text.split(None, 1)[1]
        m = await message.reply("⏳ Processing...")

        join_status = await join_assistant(message.chat.id)
        if join_status is not True:
            return await m.edit(join_status)

        await message.reply("📢 Assistant ko VC mein 'Allow to Speak' kar dein agar stream na dikhe.")
        clear_downloads()

        ydl_opts = {
            "format": "best[height<=480][ext=mp4]", 
            "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s", 
            "quiet": True,
            "noplaylist": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        await call_py.play(message.chat.id, MediaStream(file_path, video_flags=MediaStream.Flags.SCREEN_SHARE))
        await m.edit(f"🎬 **Playing:** `{info['title']}`")
    
    except Exception as e:
        logger.error(f"Play Command Error: {e}")
        await message.reply(f"❌ Play Error: {e}")

@bot.on_message(filters.command(["pause", "resume", "stop"]) & filters.group)
async def control_handler(_, message):
    try:
        cmd = message.command[0]
        if cmd == "pause":
            await call_py.pause_stream(message.chat.id)
            await message.reply("⏸ Paused.")
        elif cmd == "resume":
            await call_py.resume_stream(message.chat.id)
            await message.reply("▶️ Resumed.")
        elif cmd == "stop":
            await call_py.leave_call(message.chat.id)
            clear_downloads()
            await message.reply("⏹ Stopped.")
    except Exception as e:
        logger.error(f"Control Command Error: {e}")

# --- START ---
async def main():
    try:
        await bot.start()
        await assistant.start()
        await call_py.start()
        await start_web_server()
        logger.info("✅ Bot, Assistant & Error Handler Online!")
        await idle()
    except Exception as e:
        logger.critical(f"Startup Failed: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
