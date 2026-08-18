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
    await update.message.reply_text(
        f"👋 Салам! Мен музыкалык ботмун.\n\n"
        f"🔍 Ыр издөө үчүн: 'найти [аты]' же 'трек [аты]' деп жаз.\n"
        f"👑 Админ: {ADMIN_USER}"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_content
    user = update.effective_user
    db_users.add(user.id)
    text = update.message.text or ""

    # 1. Рассылка (админ үчүн)
    if text == "+":
        if last_content:
            for uid in db_users:
                try: await context.bot.send_message(uid, last_content)
                except: pass
            await update.message.reply_text("✅ Баарына жөнөтүлдү.")
        return

    # 2. Издөө функциясы (найти же трек)
    if text.lower().startswith(("найти ", "трек ")):
        query = text.split(maxsplit=1)[1]
        msg = await update.message.reply_text("⏳ Издөөдө...")
        
        ydl_opts = {'format': 'bestaudio', 'default_search': 'ytsearch1', 'quiet': True, 'outtmpl': 's.mp3'}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                title = info['entries'][0]['title']
                await context.bot.send_audio(update.effective_chat.id, audio=open('s.mp3', 'rb'), 
                                             title=title, caption=f"🎵 {title}\n👑 Админ: {ADMIN_USER}")
            await msg.delete()
        except:
            await msg.edit_text("❌ Ыр табылган жок.")
        return

    # 3. Админ контент сактоо
    if user.username == "Argen_70" or str(user.id) == "7648356132": # ID'ңизди тактаңыз
        last_content = text
        await update.message.reply_text("📥 Контент сакталды. '+' бассаңыз баарына тарайт.")
    else:
        await update.message.reply_text("❌")

if __name__ == "__main__":
    Thread(target=run).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot.run_polling()
