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
def run(): app.run(host='0.0.0.0', port=10000)

db_users = set()
last_content = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_users.add(update.effective_user.id)
    welcome_text = (
        "🎧 Привет! Какую песню желаешь?\n\n"
        "🔍 Просто отправь название песни (или напиши **найти [название]** / **трек [название]**), и я найду её!\n\n"
        f"👑 Администратор: {ADMIN_USER}"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_content
    user = update.effective_user
    db_users.add(user.id)
    text = update.message.text or ""

    # Рассылка админ үчүн (+ белгиси)
    if text == "+":
        if last_content:
            count = 0
            for uid in db_users:
                try:
                    if update.message.photo:
                        await context.bot.send_photo(chat_id=uid, photo=update.message.photo[-1].file_id, caption=update.message.caption)
                    else:
                        await context.bot.send_message(chat_id=uid, text=last_content)
                    count += 1
                except: pass
            await update.message.reply_text(f"✅ Рассылка отправлена {count пользователям.")
        return

    # Админ контент жөнөтсө сакталат
    if user.username == "Argen_70":
        if update.message.photo:
            last_content = update.message.caption or "Фото"
        else:
            last_content = text
        await update.message.reply_text("📥 Контент сохранен в базу. Отправьте **+** для рассылки.")
        return

    # Музыка издөө (найти, трек же жөн эле ырдын аты)
    query = text
    if text.lower().startswith("найти "):
        query = text[6:].strip()
    elif text.lower().startswith("трек "):
        query = text[5:].strip()

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
        await update.message.reply_text("❌")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))
    bot.run_polling()
