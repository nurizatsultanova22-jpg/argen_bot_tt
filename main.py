import os
import random
import yt_dlp
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

# Стилдүү, маанай көтөрүүчү вайб цитаталары (орус тилинде)
VIBE_QUOTES = [
    "🖤 Каждому треку нужен свой момент, а каждому моменту — своя музыка.",
    "🎧 Музыка — это единственный легальный способ улететь без билета.",
    "🔥 Басы күчтүү болсо, көйгөйлөр убактылуу экени билинип калат.",
    "✨ Включай трек, закрывай глаза и просто чувствуй этот вайб.",
    "🌙 Ночь, бас, акустика и ты. Больше ничего не нужно."
]

# Render порт катасын бербеши үчүн жеңил веб-сервер
app_web = Flask('')

@app_web.route('/')
def home():
    print("Ping received, bot is alive!")
    return "Bot is alive and running!"

def run_web():
    app_web.run(host='0.0.0.0', port=10000)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status = await update.message.reply_text("🔍 *Ищем твой трек, бро... Потерпи пару секунд.* ⏳", parse_mode=ParseMode.MARKDOWN)

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'track.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"scsearch1:{query}", download=True)
            track = search_results['entries'][0]
            file_path = "track.mp3"
            title = track.get('title', 'Трек')
            artist = track.get('uploader', 'Unknown Artist')

        # Кокус таасирдүү сөздү тандайбыз
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
        await status.edit_text("❌ *Брат, этот трек спрятался. Попробуй написать другое название!*", parse_mode=ParseMode.MARKDOWN)

if __name__ == "__main__":
    # Веб-серверди фондо жандырабыз (Render үчүн)
    t = Thread(target=run_web)
    t.start()
    
    # Telegram ботту иштей түшүрөбүз
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🔥 Бот в стиле и готов разрывать!")
    app.run_polling()
