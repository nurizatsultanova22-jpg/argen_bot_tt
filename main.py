import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status = await update.message.reply_text("⏳ Изделип жатат...")

    try:
        # YouTube бөгөтүнөн өтүү үчүн кошумча параметрлер
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'song.%(ext)s',
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            video_info = info['entries'][0]
            file_path = "song.mp3"

        # Аудиону жөнөтүү
        await update.message.reply_audio(
            audio=open(file_path, 'rb'),
            title=video_info.get('title', 'Музыка'),
            performer=video_info.get('uploader', 'Argen Bot')
        )
        
        await status.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await status.edit_text("❌ Тилекке каршы, бул ырды жүктөөгө YouTube уруксат берген жок. Башка ыр жазып көрүңүз.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
