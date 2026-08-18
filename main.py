import os
import time
import random
import threading
import schedule
import telebot
from flask import Flask

# 1. Веб-сервер (Render иштеши үчүн)
app = Flask('')

@app.route('/')
def home():
    return "Bot status: Online"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. Бот токени жана Канал
TOKEN = '8817519388:AAH05Kz22gJ5bey4m-9p0TwiSmme7WGmnz4'
CHANNEL_ID = '@kinoru_kgz'

bot = telebot.TeleBot(TOKEN)

# 3. /start командасы
@bot.message_handler(commands=['start'])
def send_welcome(message):
    reply_text = (
        "✨ *Арген, ты официально признан лучшим IT-специалистом!* 💻🚀\n\n"
        "Желаю тебе достигать новых невероятных высот! 💫🔥"
    )
    bot.send_message(message.chat.id, reply_text, parse_mode='Markdown')

# 4. /test командасы (Каналды текшерүү үчүн)
@bot.message_handler(commands=['test'])
def test_post(message):
    try:
        send_post()
        bot.reply_to(message, "✅ Пост каналга ийгиликтүү жөнөтүлдү!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ката чыкты: {e}")

# Посттор жана сүрөттөр
MESSAGES = [
    "🖤 *Твои глаза — мой самый любимый омут...*\n\nВ них столько жизни! ✨",
    "🏎 *Скорость в венах, ночные огни...*\n\nВ этом городе мы с тобой одни. 🔥",
    "🤍 *Держи меня за руку крепче, чем прежде,*\n\nВ мире, где так мало искренней надежды. 🕊"
]

IMAGE_URLS = [
    "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?q=80&w=1000",
    "https://images.unsplash.com/photo-1503376780353-7e6692767b70?q=80&w=1000"
]

def send_post():
    bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=random.choice(IMAGE_URLS),
        caption=random.choice(MESSAGES),
        parse_mode='Markdown'
    )

schedule.every(1).hours.do(send_post)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=run_schedule, daemon=True).start()
    
    print("Бот ишке кирди...")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
