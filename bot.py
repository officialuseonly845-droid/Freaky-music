import os
import shutil
import asyncio
from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
import yt_dlp
from aiohttp import web

# --- CONFIG (Render Environment Variables se lega) ---
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

# --- UPTIME SERVER (Render ko 24/7 jagaye rakhne ke liye) ---
async def health_check(request):
    return web.Response(text="Bot is Alive!")

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
    except Exception:
        try:
            invite_link = await bot.export_chat_invite_link(chat_id)
            await assistant.join_chat(invite_link)
        except Exception as e:
            return f"❌ Assistant join nahi kar paya. Bot ko Admin banayein! Error: {e}"
    return True

def clear_downloads():
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
        os.makedirs(DOWNLOAD_DIR)

# --- COMMANDS ---

@bot.on_message(filters.command("play") & filters.group)
async def play_handler(_, message):
    if len(message.command) < 2:
        return await message.reply("❌ Usage: `/play <link>`")
    
    url = message.text.split(None, 1)[1]
    m = await message.reply("⏳ Assistant check ho raha hai...")

    if await join_assistant(message.chat.id) is not True:
        return await m.edit("❌ Assistant group join nahi kar paya.")

    # Non-admin assistant reminder
    await message.reply("📢 **Note:** Agar assistant mute hai, toh use VC mein 'Allow to Speak' rights dein.")

    clear_downloads()

    ydl_opts = {
        "format": "best[height<=480][ext=mp4]", 
        "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s", 
        "quiet": True,
        "noplaylist": True
    }

    try:
        await m.edit("📥 Downloading (480p)...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info['duration'] > 3600:
                return await m.edit("❌ Video 1 ghante se lambi hai!")
            file_path = ydl.prepare_filename(info)

        await call_py.play(message.chat.id, MediaStream(file_path, video_flags=MediaStream.Flags.SCREEN_SHARE))
        await m.edit(f"🎬 **Playing:** `{info['title']}`\n\n⏸ /pause | ▶️ /resume | ⏹ /stop")
    except Exception as e:
        await m.edit(f"❌ Error: {str(e)[:100]}...")

@bot.on_message(filters.command("pause") & filters.group)
async def pause_handler(_, message):
    try:
        await call_py.pause_stream(message.chat.id)
        await message.reply("⏸ **Paused.**")
    except: pass

@bot.on_message(filters.command("resume") & filters.group)
async def resume_handler(_, message):
    try:
        await call_py.resume_stream(message.chat.id)
        await message.reply("▶️ **Resumed.**")
    except: pass

@bot.on_message(filters.command("stop") & filters.group)
async def stop_handler(_, message):
    try:
        await call_py.leave_call(message.chat.id)
        clear_downloads()
        await message.reply("⏹ **Stopped & Cleaned.**")
    except: pass

# --- START BOT ---
async def main():
    await bot.start()
    await assistant.start()
    await call_py.start()
    await start_web_server()
    print("✅ Bot and Assistant are Online!")
    await idle()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
