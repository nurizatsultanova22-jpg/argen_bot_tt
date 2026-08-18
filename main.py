import os
import time
import random
import threading
import schedule
import telebot
from flask import Flask

# 1. Render порт таппай жатканы үчүн жөнөкөй веб-сервер
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

# Личкада /start баскандагы жооп
@bot.message_handler(commands=['start'])
def send_welcome(message):
    reply_text = (
        "✨ *Арген, ты официально признан лучшим IT-специалистом!* 💻🚀\n\n"
        "Желаю тебе достигать новых невероятных высот, легко покорять "
        "любые вершины программирования и создавать самые крутые проекты! "
        "Пусть каждый твой код работает идеально, без единой ошибки. 💫🔥"
    )
    gif_url = "https://media.giphy.com/media/qgQUGGAC3P4vC/giphy.gif"
    
    try:
        bot.send_animation(
            chat_id=message.chat.id,
            animation=gif_url,
            caption=reply_text,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Ката: {e}")

# Каналга посттор
MESSAGES = [
    "🖤 *Твои глаза — мой самый любимый омут...*\n\nВ них столько жизни, страсти и огня. 🥀\nИ если все на свете где-то тонут,\nТо я тону, смотря лишь на тебя. ✨",
    "🏎 *Скорость в венах, ночные огни...*\n\nВ этом городе мы с тобой одни. 🔥\nЧерный глянец, рев мотора и мост,\nДолетим до самых далеких звезд. ⚡️",
    "🤍 *Держи меня за руку крепче, чем прежде,*\n\nВ мире, где так мало искренней надежды. 🕊\nПусть вечер подарит тепло и покой,\nГлавное счастье — быть рядом с тобой. ✨"
]

IMAGE_URLS = [
    "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?q=80&w=1000",
    "https://images.unsplash.com/photo-1503376780353-7e6692767b70?q=80&w=1000",
    "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1000"
]

def send_post():
    try:
        bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=random.choice(IMAGE_URLS),
            caption=random.choice(MESSAGES),
            parse_mode='Markdown'
        )
        print("Пост каналга жөнөтүлдү!")
    except Exception as e:
        print(f"Каналга жөнөтүүдө ката: {e}")

schedule.every(1).hours.do(send_post)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    # Flask серверин өзүнчө агымда баштоо (Render портту көрсүн үчүн)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Пост графигин баштоо
    threading.Thread(target=run_schedule, daemon=True).start()
    
    # Ботту иштетүү
    print("Бот ишке кирди...")
    bot.remove_webhook()
    time.sleep(1)
    
    bot.infinity_polling(skip_pending=True)
