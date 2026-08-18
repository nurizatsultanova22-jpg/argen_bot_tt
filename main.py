import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from threading import Thread
from flask import Flask
import yt_dlp

TOKEN = "8817519388:AAH05Kz22gJ5bey4m-9p0TwiSmme7WGmnz4"
ADMIN_USER = "@Argen_70"

app = Flask('')
@app.route('/')
def home(): return "Бот работает!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

db_users = set()
saved_content = {"type": None, "file_id": None, "caption": None, "text": None}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_users.add(update.effective_user.id)
    welcome_text = (
        "🎧 Привет! Какую песню желаешь?\n\n"
        "🔍 Напиши **трек [название]** или **найти [название]**, и я найду трек с обложкой!\n\n"
        f"👑 Администратор: {ADMIN_USER}"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_content
    user = update.effective_user
    db_users.add(user.id)
    text = update.message.text or update.message.caption or ""

    # Админ текшерүү (юзернейм аркылуу)
    is_admin = (user.username == "Argen_70")

    # 1. Рассылка (+)
    if text == "+" and is_admin:
        if saved_content["type"]:
            count = 0
            for uid in db_users:
                try:
                    if saved_content["type"] == "photo":
                        await context.bot.send_photo(chat_id=uid, photo=saved_content["file_id"], caption=saved_content["caption"])
                    elif saved_content["type"] == "video":
                        await context.bot.send_video(chat_id=uid, video=saved_content["file_id"], caption=saved_content["caption"])
                    elif saved_content["type"] == "text":
                        await context.bot.send_message(chat_id=uid, text=saved_content["text"])
                    count += 1
                except: pass
            await update.message.reply_text(f"✅ Реклама успешно отправлена пользователям: {count}")
        else:
            await update.message.reply_text("⚠️ Сначала отправьте фото, видео или текст для рекламы.")
        return

    # 2. Админ контент сактоо (сүрөт, видео же текст)
    if is_admin and text != "+":
        if update.message.photo:
            saved_content = {"type": "photo", "file_id": update.message.photo[-1].file_id, "caption": update.message.caption, "text": None}
            await update.message.reply_text("📥 Фото сохранено в базу! Отправьте **+** для рассылки.")
            return
        elif update.message.video:
            saved_content = {"type": "video", "file_id": update.message.video.file_id, "caption": update.message.caption, "text": None}
            await update.message.reply_text("📥 Видео сохранено в базу! Отправьте **+** для рассылки.")
            return
        elif text and not text.lower().startswith(("трек ", "найти ")):
            saved_content = {"type": "text", "file_id": None, "caption": None, "text": text}
            await update.message.reply_text("📥 Текст сохранен в базу! Отправьте **+** для рассылки.")
            return

    # 3. Музыка издөө (трек же найти)
    query = ""
    if text.lower().startswith("трек "):
        query = text[5:].strip()
    elif text.lower().startswith("найти "):
        query = text[6:].strip()

    if query:
        status_msg = await update.message.reply_text("⏳ Подаждите, ищу трек... [3 сек]")
        await asyncio.sleep(1)
        try: await status_msg.edit_text("⏳ Подаждите, ищу трек... [2 сек]")
        except: pass
        await asyncio.sleep(1)
        try: await status_msg.edit_text("⏳ Подаждите, ищу трек... [1 сек]")
        except: pass

        ydl_opts = {
            'format': 'bestaudio',
            'default_search': 'scsearch1',
            'quiet': True,
            'outtmpl': 'song.mp3',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"scsearch1:{query}", download=True)
                if 'entries' in info:
                    info = info['entries'][0]
                title = info.get('title', 'Музыка')

            keyboard = [
                [
                    InlineKeyboardButton("❤️ Огонь 🔥", callback_data="like_fire"),
                    InlineKeyboardButton("💪 Мощь 🚀", callback_data="like_power")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            caption_text = f"🎵 {title}\n\n✨ Отличный трек!\n👑 Админ: {ADMIN_USER}"

            with open("song.mp3", 'rb') as audio:
                await update.message.reply_audio(
                    audio=audio,
                    title=title,
                    caption=caption_text,
                    reply_markup=reply_markup
                )
            await status_msg.delete()
            if os.path.exists("song.mp3"): os.remove("song.mp3")
        except:
            await status_msg.edit_text(f"❌ Трек не найден!\n👑 Админ: {ADMIN_USER}")
    else:
        if not is_admin:
            await update.message.reply_text("❌ Напишите **трек [название]** или **найти [название]**.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))
    bot.run_polling()
