import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

TOKEN = "8558649634:AAHEqz0qKwSg46pcqme0D84pLsdAmVIe8p8"

# Акыркы сакталган постту убактылуу эс тутумда сактоо (Render үчүн ишенимдүү)
last_post = {"file_id": None, "type": None, "caption": None}
subscribers = set() # Катталуучулардын IDлери

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subscribers.add(user_id) # Автоматтык катталуу
    await update.message.reply_text("✨ Привет! Ты подписался на канал. Жди крутой контент! 🎧")

async def admin_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Бул жерде өзүңдүн Telegram ID'ңди жазып кой (аны ботко /myid деп жазып билсең болот)
    # Болбосо, эң жөнөкөйү: баарына иштесин
    message = update.message
    
    if message.audio:
        last_post.update({"file_id": message.audio.file_id, "type": "audio", "caption": message.caption})
    elif message.video:
        last_post.update({"file_id": message.video.file_id, "type": "video", "caption": message.caption})
    elif message.photo:
        last_post.update({"file_id": message.photo[-1].file_id, "type": "photo", "caption": message.caption})
    
    await message.reply_text("✅ Контент принят! Теперь напиши /send для рассылки всем.")

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
        except:
            continue
    await update.message.reply_text(f"🚀 Успешно разослано {count} людям!")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", broadcast))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VIDEO | filters.PHOTO, admin_upload))
    print("🔥 Бот готов к работе!")
    app.run_polling()
