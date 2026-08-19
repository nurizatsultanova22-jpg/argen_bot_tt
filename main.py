import os
import random
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

# Тынчылыкты жана маанайды көтөрүүчү таасирдүү сөзыркмахтар (цитаты)
VIBE_QUOTES = [
    "🖤 Каждому треку нужен свой момент, а каждому моменту — своя музыка.",
    "🎧 Музыка — это единственный легальный способ улететь без билета.",
    "🔥 Басы күчтүү болсо, көйгөйлөр убактылуу экени билинип калат.",
    "✨ Включай трек, закрывай глаза и просто чувствуй этот вайб.",
    "🌙 Ночь, бас, акустика и ты. Больше ничего не нужно."
]

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

        # Таасирдүү сөздөрдү кокус түррө тандап алабыз
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
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🔥 Бот в стиле и готов разрывать!")
    app.run_polling()
