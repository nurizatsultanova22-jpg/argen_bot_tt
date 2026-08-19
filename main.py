import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# Сиздин акыркы токениңиз
TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Салам! Ырдын же клиптин атын жазыңыз, мен аны толук версияда таап берем.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status = await update.message.reply_text("⏳ Издөө жана жүктөө жүрүп жатат...")

    try:
        # YouTube'дан издөө жана жүктөө үчүн эң туруктуу конфигурация
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'download.%(ext)s',
            'quiet': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            video_info = info['entries'][0]
            file_path = "download.mp4" 

        # Видеону жана аудиону жөнөтүү
        await update.message.reply_video(video=open(file_path, 'rb'), caption=f"🎥 {video_info['title']}")
        await update.message.reply_audio(audio=open(file_path, 'rb'), title=video_info['title'])

        await status.delete()
        if os.path.exists(file_path): os.remove(file_path)

    except Exception:
        await status.edit_text("❌ Ката чыкты. Ыр табылбады же серверде көйгөй бар.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
