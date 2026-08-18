import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, CommandHandler, filters, ContextTypes
import yt_dlp
from flask import Flask
from threading import Thread

# Конфигурация
TELEGRAM_BOT_TOKEN = "8817519388:AAH05Kz22gJ5bey4m-9p0TwiSmme7WGmnz4"

# Веб-сервер бөлүгү (Render порт талап кылбашы үчүн)
app_web = Flask('')
@app_web.route('/')
def home():
    return "Бот иштеп жатат!"

def run_web():
    app_web.run(host='0.0.0.0', port=10000)

# /start буйругу келгенде
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    chat_id = update.effective_chat.id
    
    welcome_text = (
        f"Добро пожаловать, {user_name}! 🎧\n"
        "Какую музыку вы хотите послушать?\n\n"
        "👉 Напишите слово **найти** и название песни."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")
    context.job_queue.run_once(send_group_promo, 120, chat_id=chat_id)

async def send_group_promo(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    promo_text = "💡 Кстати, вы можете использовать меня и в группах! Добавьте меня в свою группу, чтобы слушать музыку вместе с друзьями."
    await context.bot.send_message(chat_id=chat_id, text=promo_text)

# Музыканы тезирээк табуу жана жүрөкчөлөрдү кошуу
async def download_and_send_audio(chat_id, query, context):
    # Тезирээк табуу үчүн yt-dlp параметрлерин оптималдаштыруу
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'scsearch1',
        'writethumbnail': True,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128', # Качествону оптималдуу кылып ылдамдыгын жогорулатуу
            }
        ],
        'outtmpl': 'song',
    }
    
    try:
        status_msg = await context.bot.send_message(chat_id=chat_id, text=f"⚡ Изем: {query}...")
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            
            title = info.get('title', 'Оригинальный трек')
            
        # Жүктөлгөн абалда билдирүүнү өчүрүү (тездетүү максатында)
        await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
            
        thumb_file = None
        for ext in ['.jpg', '.webp', '.png', '.jpeg']:
            if os.path.exists(f"song{ext}"):
                thumb_file = f"song{ext}"
                break
        
        # Жүрөк жана жараланган жүрөк баскычтары (Inline buttons)
        keyboard = [
            [
                InlineKeyboardButton("❤️", callback_data="like_heart"),
                InlineKeyboardButton("💔", callback_data="like_broken")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        caption_text = f"🎵 {title}\n\n✨ Ботко кош келдиңиз!"

        with open("song.mp3", 'rb') as audio:
            if thumb_file:
                with open(thumb_file, 'rb') as thumb:
                    await context.bot.send_audio(
                        chat_id=chat_id,
                        audio=audio,
                        thumbnail=thumb,
                        title=title,
                        caption=caption_text,
                        reply_markup=reply_markup
                    )
            else:
                await context.bot.send_audio(
                    chat_id=chat_id,
                    audio=audio,
                    caption=caption_text,
                    reply_markup=reply_markup
                )
                
        if os.path.exists("song.mp3"):
            os.remove("song.mp3")
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)
            
    except Exception as e:
        print(f"Ошибка: {e}")
        await context.bot.send_message(chat_id=chat_id, text="❌ Кечиресиз, ырды табууда ката кетти. Башка ат менен жазып көрүңүз.")

# Баскычтарды басканда эмодзи кошуу функциясы
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    original_caption = query.message.caption or ""
    
    if query.data == "like_heart":
        # Эгер жүрөктү басса
        new_caption = original_caption + "\n\n❤️ Укмуш сонун ыр!"
        try:
            await query.edit_message_caption(caption=new_caption, reply_markup=query.message.reply_markup)
        except Exception:
            pass
            
    elif query.data == "like_broken":
        # Эгер жараланган жүрөктү басса
        new_caption = original_caption + "\n\n💔 Муenюс сонун эмес экен"
        try:
            await query.edit_message_caption(caption=new_caption, reply_markup=query.message.reply_markup)
        except Exception:
            pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower().startswith("найти"):
        query = text[5:].strip()
        if query:
            await download_and_send_audio(update.effective_chat.id, query, context)
        else:
            await update.message.reply_text("⚠️ Ырдын атын кошо жазыңыз. Мисалы: *найти Bakr*")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Бот иштеп жатат...")
    app.run_polling()
