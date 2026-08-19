import logging
import yt_dlp
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from telegram.constants import ParseMode

# Сенин токениң
TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

# Маалыматтар
subscribers = set()
last_post = {"file_id": None, "type": None, "caption": None}

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subscribers.add(user_id)
    await update.message.reply_text("✨ Привет! Бот готов. Отправь название песни или админ-контент! 🎧")

# Админ контентти кабыл алат
async def admin_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg.audio:
        last_post.update({"file_id": msg.audio.file_id, "type": "audio", "caption": msg.caption})
    elif msg.video:
        last_post.update({"file_id": msg.video.file_id, "type": "video", "caption": msg.caption})
    elif msg.photo:
        last_post.update({"file_id": msg.photo[-1].file_id, "type": "photo", "caption": msg.caption})
    else:
        return
    await msg.reply_text("✅ Принято! Пиши /send для рассылки.")

# Рассылка (баарына жөнөтүү)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not last_post["file_id"]:
        await update.message.reply_text("❌ Нет контента.")
        return
    
    count = 0
    for user_id in subscribers:
        try:
            if last_post["type"] == "audio":
                await context.bot.send_audio(user_id, last_post["file_id"], caption=last_post["caption"])
            elif last_post["type"] == "video":
                await context.bot.send_video(user_id, last_post["file_id"], caption=last_post["caption"])
            elif last_post["type"] == "photo":
                await context.bot.send_photo(user_id, last_post["file_id"], caption=last_post["caption"])
            count += 1
        except: continue
    await update.message.reply_text(f"🚀 Разослано: {count}")

# Ыр издөө
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status = await update.message.reply_text("🔍 Ищу...")
    try:
        ydl_opts = {'format': 'bestaudio', 'quiet': True, 'outtmpl': 'track.mp3'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(f"scsearch1:{query}", download=True)
            track = res['entries'][0]
            await update.message.reply_audio(audio=open('track.mp3', 'rb'), title=track['title'])
            await status.delete()
            os.remove('track.mp3')
    except:
        await status.edit_text("❌ Не нашел.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", broadcast))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VIDEO | filters.PHOTO, admin_upload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    print("🚀 Бот запущен!")
    app.run_polling()
