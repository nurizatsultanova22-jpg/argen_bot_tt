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
    user_name = update.effective_user.first_name
    chat_id = update.effective_chat.id
    welcome_text = (
        f"👋 Привет, {user_name}! Я твой музыкальный друг! 🎶\n\n"
        "👉 Напиши **найти** и название песни (например: *найти камин*)\n"
        "🎮 Или напиши **игра**, чтобы поиграть в угадайку!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")
    context.job_queue.run_once(send_group_promo, 120, chat_id=chat_id)

async def send_group_promo(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=context.job.chat_id, text="💡 Кстати, вы можете использовать меня и в группах! Добавьте меня в свою группу.")

async def download_and_send_audio(chat_id, query, context):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'auto',
        'q': True,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}],
        'outtmpl': 'song.mp3',
    }
    
    status_msg = await context.bot.send_message(chat_id=chat_id, text=f"🔍 Ищу трек: {query}... 🏃‍♂️💨")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Туura издөө сурамы
            search_query = f"ytsearch:{query}"
            info = ydl.extract_info(search_query, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            title = info.get('title', 'Музыка')
        
        keyboard = [[InlineKeyboardButton("❤️", callback_data="like_heart"), InlineKeyboardButton("💔", callback_data="like_broken")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        with open("song.mp3", 'rb') as audio:
            await context.bot.send_audio(
                chat_id=chat_id, 
                audio=audio, 
                title=title, 
                caption=f"🎧 Нашел! {title}\n\n✨ Приятного прослушивания!", 
                reply_markup=reply_markup
            )
        
        await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
        if os.path.exists("song.mp3"): os.remove("song.mp3")
            
    except Exception as e:
        print(f"Error: {e}")
        await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="😢 Ой, не смог найти этот трек... Попробуй написать точнее! 🥺")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    original_caption = query.message.caption or ""
    if query.data == "like_heart":
        try:
            await query.edit_message_caption(caption=original_caption + "\n\n❤️ Ого, крутой вкус! 😍", reply_markup=query.message.reply_markup)
        except: pass
    elif query.data == "like_broken":
        try:
            await query.edit_message_caption(caption=original_caption + "\n\n💔 Жаль... Буду искать лучше! 😔", reply_markup=query.message.reply_markup)
        except: pass

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_games[chat_id] = random.randint(1, 10)
    await update.message.reply_text("🎲 Давай сыграем! Я загадал число от 1 до 10. Угадаешь? 🤔 Текст же отправь цифру!")

async def check_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in user_games:
        try:
            guess = int(update.message.text)
            if guess == user_games[chat_id]:
                await update.message.reply_text("🏆 Ура! Ты гений, угадал число! 🎉🥳")
                del user_games[chat_id]
            else:
                await update.message.reply_text("🙊 Не-а! Попробуй еще разок, я верю в тебя! 💪")
        except: pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower().startswith("найти"):
        query = text[5:].strip()
        if query:
            await download_and_send_audio(update.effective_chat.id, query, context)
        else:
            await update.message.reply_text("⚠️ Напишите название после слова найти!")
    elif text.lower() == "игра":
        await start_game(update, context)
    elif text.isdigit():
        await check_guess(update, context)

if __name__ == "__main__":
    t = Thread(target=run_web); t.start()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
