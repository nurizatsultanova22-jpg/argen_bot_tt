import os
import threading
import requests
from flask import Flask
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    
    # "найди" же "трек" менен башталбаса иштебейт
    if not (text.startswith("найди") or text.startswith("трек")):
        return  

    query = text.replace("найди", "").replace("трек", "").strip()
    if not query:
        return

    status = await update.message.reply_text("🔍 *Ищу трек...* 🎧", parse_mode=ParseMode.MARKDOWN)

    try:
        # Piped API аркылуу издөө
        search_url = f"https://pipedapi.kavin.rocks/search?q={query}"
        response = requests.get(search_url, timeout=10).json()
        items = [i for i in response.get('items', []) if i['type'] == 'stream']

        if not items:
            await status.edit_text("❌ *Трек не найден.*", parse_mode=ParseMode.MARKDOWN)
            return

        video_url = f"https://www.youtube.com/watch?v={items[0]['url'].split('=')[-1]}"
        title = items[0].get('title', 'Трек')
        artist = items[0].get('uploaderName', 'Unknown')

        # Жүктөө
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'track.mp3',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        await update.message.reply_audio(
            audio=open('track.mp3', 'rb'),
            title=title,
            performer=artist,
            caption=f"🎵 **{artist} — {title}**\n\n⚡ *Created by Argen*",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await status.delete()
        if os.path.exists('track.mp3'): os.remove('track.mp3')

    except Exception:
        await status.edit_text("❌ *Ошибка при поиске.*", parse_mode=ParseMode.MARKDOWN)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
