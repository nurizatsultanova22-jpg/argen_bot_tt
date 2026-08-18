import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, CommandHandler, filters, ContextTypes
import yt_dlp
from flask import Flask
from threading import Thread

TELEGRAM_BOT_TOKEN = "8817519388:AAH05Kz22gJ5bey4m-9p0TwiSmme7WGmnz4"

app_web = Flask('')
@app_web.route('/')
def home(): return "Бот работает!"
def run_web(): app_web.run(host='0.0.0.0', port=10000)

user_games = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я твой SoundCloud-бот! 🎶\nНапиши 'найти [песня]' или 'игра'.")

async def download_and_send_audio(chat_id, query, context):
    # SoundCloud үчүн атайын жөндөөлөр
    ydl_opts = {
        'format': 'bestaudio',
        'noplaylist': True,
        'default_search': 'scsearch1', # SoundCloud'дан издейт
        'quiet': True,
        'outtmpl': 'song.mp3',
    }
    
    status_msg = await context.bot.send_message(chat_id=chat_id, text=f"🔍 Ищу на SoundCloud: {query}... 🎧")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # scsearch1: колдонуучунун сурамын SoundCloud'дан издейт
            info = ydl.extract_info(f"scsearch1:{query}", download=True)
            if 'entries' in info:
                info = info['entries'][0]
            
            title = info.get('title', 'Музыка с SoundCloud')
        
        with open("song.mp3", 'rb') as audio:
            await context.bot.send_audio(chat_id=chat_id, audio=audio, title=title, caption=f"🎵 {title}\n\n✨ Найдено на SoundCloud!")
        
        await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
        if os.path.exists("song.mp3"): os.remove("song.mp3")
            
    except Exception as e:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="😢 Не удалось найти на SoundCloud. Попробуй другое название.")

# ... (Оюн функциялары өзгөрүүсүз калат) ...
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_games[chat_id] = random.randint(1, 10)
    await update.message.reply_text("🎲 Загадал число от 1 до 10. Угадаешь?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower().startswith("найти"):
        await download_and_send_audio(update.effective_chat.id, text[5:].strip(), context)
    elif text.lower() == "игра":
        await start_game(update, context)
    elif text.isdigit():
        chat_id = update.effective_chat.id
        if chat_id in user_games and int(text) == user_games[chat_id]:
            await update.message.reply_text("🏆 Ура! Угадал!")
            del user_games[chat_id]
        else:
            await update.message.reply_text("🙊 Не-а! Еще раз?")

if __name__ == "__main__":
    t = Thread(target=run_web); t.start()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
