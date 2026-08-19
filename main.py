import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status = await update.message.reply_text("⏳ Ырдын толук версиясы изделүүдө...")

    try:
        # SoundCloud аркылуу толук тректи жүктөө (YouTube сыяктуу бөгөт койбойт)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'full_song.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # scsearch аркылуу SoundCloud'дан издөө
            search_results = ydl.extract_info(f"scsearch1:{query}", download=True)
            track = search_results['entries'][0]
            file_path = "full_song.mp3"
            title = track.get('title', 'Музыка')
            artist = track.get('uploader', 'Argen')

        # Толук ырды жөнөтүү
        await update.message.reply_audio(
            audio=open(file_path, 'rb'),
            title=title,
            performer=artist
        )
        
        await status.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await status.edit_text("❌ Кечиресиз, толук версиясы табылган жок.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
