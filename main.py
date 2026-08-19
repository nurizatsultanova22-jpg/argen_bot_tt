import os
import logging
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from telegram.constants import ParseMode

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

last_post = {"file_id": None, "type": None, "caption": None}
subscribers = set()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subscribers.add(user_id)
    await update.message.reply_text("✨ Привет! Добро пожаловать в наш бот. Отправь название трека или жди крутой контент! 🎧", parse_mode=ParseMode.MARKDOWN)

# Администратор контент жөнөткөндө (Сүрөт, Видео, Аудио)
async def admin_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    subscribers.add(update.effective_user.id)
    
    if message.audio:
        last_post.update({"file_id": message.audio.file_id, "type": "audio", "caption": message.caption})
        await message.reply_text("✅ Аудио принято! Отправь /send для рассылки.")
    elif message.video:
        last_post.update({"file_id": message.video.file_id, "type": "video", "caption": message.caption})
        await message.reply_text("✅ Видео принято! Отправь /send для рассылки.")
    elif message.photo:
        last_post.update({"file_id": message.photo[-1].file_id, "type": "photo", "caption": message.caption})
        await message.reply_text("✅ Фото принято! Отправь /send для рассылки.")

# Рассылка кылуу
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not last_post["file_id"]:
        await update.message.reply_text("❌ Нет контента для рассылки.")
        return

    count = 0
    for user_id in subscribers:
        try:
            if last_post["type"] == "audio":
                await context.bot.send_audio(chat_id=user_id, audio=last_post["file_id"], caption=last_post["caption"])
            elif last_post["type"] == "video":
                await context.bot.send_video(chat_id=user_id, video=last_post["file_id"], caption=last_post["caption"])
            elif last_post["type"] == "photo":
                await context.bot.send_photo(chat_id=user_id, photo=last_post["file_id"], caption=last_post["caption"])
            count += 1
        except Exception:
            continue
            
    await update.message.reply_text(f"🚀 Успешно разослано людям: {count}!")

# Жөнөкөй текст жазганда музыка издөө функциясы
async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    subscribers.add(update.effective_user.id)
    
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

        caption = f"🎵 **{artist} — {title}**\n\n✨ *Специально для тебя*\n👤 *Created by Argen*"

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
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", broadcast))
    
    # Сүрөт, видео же ыр жөнөтсө админски контент катары кабыл алат
    app.add_handler(MessageHandler(filters.AUDIO | filters.VIDEO | filters.PHOTO, admin_upload))
    
    # Кандайдыр бир текст (мисалы "Камин") жазса ыр издейт
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search_music))

    print("🔥 Бот с поиском музыки и рассылкой запущен!")
    app.run_polling()
