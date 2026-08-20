import os
import threading
import requests
from flask import Flask
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

TOKEN = "8845409356:AAFjm-nh9q_aWPyfUVHx8v0k-sHYeFtoJgA"

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    
    if not (text.startswith("найди") or text.startswith("трек")):
        return  

    query = text.replace("найди", "").replace("трек", "").strip()
    if not query:
        return

    status = await update.message.reply_text("🔍 *Ищу трек...* 🎧", parse_mode=ParseMode.MARKDOWN)

    try:
        # 1. Deezer аркылуу сүрөт (фон) табуу
        deezer_url = f"https://api.deezer.com/search?q={query}"
        deezer_res = requests.get(deezer_url).json()
        
        cover_image = None
        if 'data' in deezer_res and len(deezer_res['data']) > 0:
            track_info = deezer_res['data'][0]
            cover_image = track_info['album']['cover_big']

        # 2. SoundCloud аркылуу толук MP3 файлды жүктөө
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'track.mp3',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True,
            'default_search': 'scsearch1:',
            'noplaylist': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch1:{query}", download=True)
            if 'entries' in info:
                info = info['entries'][0]
            
            title = info.get('title', 'Трек')
            artist = info.get('uploader', 'Music')

        caption_text = f"🎵 **{artist} — {title}**\n\n⚡ *Created by Argen*"
        
        # Эгер Deezer сүрөтү табылса, алгач сүрөттү (фонду) жиберебиз
        if cover_image:
            await update.message.reply_photo(
                photo=cover_image,
                caption=f"🖼 **Обложка**\n🎵 {artist} — {title}",
                parse_mode=ParseMode.MARKDOWN
            )

        # Анан SoundCloud'дон келген толук аудио файлды жиберебиз
        await update.message.reply_audio(
            audio=open('track.mp3', 'rb'),
            title=title,
            performer=artist,
            caption=caption_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        await status.delete()
        if os.path.exists('track.mp3'): 
            os.remove('track.mp3')

    except Exception:
        await status.edit_text("❌ *Трек не найден. Попробуй другое название!*", parse_mode=ParseMode.MARKDOWN)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
