import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

# SoundCloud үчүн оптимизацияланган параметрлер
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
    'quiet': True,
    'no_warnings': True,
    'outtmpl': 'song.mp3'
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if not query: return
    
    status = await update.message.reply_text("🔍 Издейм...")
    
    try:
        # scsearch: SoundCloud'дан гана издейт
        with yt_dlp.YoutubeDL({'default_search': 'scsearch1', 'quiet': True}) as ydl:
            results = ydl.extract_info(f"scsearch1:{query}", download=False)
            entry = results['entries'][0]
        
        # Ырды жүктөө
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            ydl.download([entry['webpage_url']])
        
        # Telegram'га жөнөтүү
        if os.path.exists('song.mp3'):
            await update.message.reply_audio(
                audio=open('song.mp3', 'rb'),
                title=entry.get('title', 'Музыка'),
                performer=entry.get('uploader', 'SoundCloud'),
                caption=f"🎵 {entry.get('title')}"
            )
            os.remove('song.mp3')
            await status.delete()
        else:
            await status.edit_text("❌ Файл табылган жок.")
            
    except Exception as e:
        await status.edit_text("❌ Ыр табылган жок же ката чыкты.")

if __name__ == "__main__":
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app_bot.run_polling()
