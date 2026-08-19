import os
import random
import threading
from flask import Flask
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

# Веб-сервер (Render үчүн)
app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Bot is active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

# Вайб цитаталары
VIBE_QUOTES = [
    "🖤 Каждому треку нужен свой момент, а каждому моменту — своя музыка.",
    "🎧 Музыка — это единственный легальный способ улететь без билета.",
    "🔥 Басы күчтүү болсо, көйгөйлөр убактылуу экени билинип калат.",
    "✨ Включай трек, закрывай глаза и просто чувствуй этот вайб.",
    "🌙 Ночь, бас, акустика и ты. Больше ничего не нужно."
]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    
    # "найди" же "трек" сөзү менен башталышын текшеребиз
    if not text.startswith("найди") and not text.startswith("трек"):
        return  # Эгер бул сөздөр жок болсо, бот такыр жооп бербейт

    # "найди" же "трек" деген сөздөрдү алып салып, таза атын калтырабыз
    query = text.replace("найди", "").replace("трек", "").strip()
    
    if not query:
        await update.message.reply_text("⚠️ *Брат, после слова 'найди' или 'трек' напиши название песни!*", parse_mode=ParseMode.MARKDOWN)
        return

    status = await update.message.reply_text("🔍 *Ищу на YouTube Music...* 🎧", parse_mode=ParseMode.MARKDOWN)

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'track.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True,
            'noplaylist': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytmsearch1:{query}", download=True)
            track = search_results['entries'][0]
            file_path = "track.mp3"
            title = track.get('title', 'Трек')
            artist = track.get('uploader', 'Music').replace(" - Topic", "")

        random_quote = random.choice(VIBE_QUOTES)
        
        caption = (
            f"🎵 **{artist} — {title}**\n\n"
            f"{random_quote}\n\n"
            f"⚡ *Специально для тебя*\n"
            f"👤 *Created by Argen*"
        )

        await update.message.reply_audio(
            audio=open(file_path, 'rb'),
            title=title,
            performer=artist,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN
        )
        
        await status.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception:
        await status.edit_text("❌ *Брат, музыка не найдена. Попробуй другое название!*", parse_mode=ParseMode.MARKDOWN)

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
