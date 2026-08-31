import os
import asyncio
import threading
import time
import random
import telebot
from aiohttp import web

TOKEN = "8387252723:AAGSgqC0yOJ2X-qAcgAIr0WsL7rnjIUyUGc"

bot = telebot.TeleBot(TOKEN)

welcomed_users = set()
last_message_time = {}
user_replied = set()

smart_replies = [
    "Туура айтасыз, досум! 🤝 Бул тууралуу Арген келгенде толук сүйлөшөбүз.",
    "Кызыктуу суроо экен! 🤔 Арген өзү келгенде бул маселени чогуу талкуулайбыз.",
    "Макул, түшүндүм! 🫡 Аргенге бул тууралуу ошол замат кабарлап коём.",
    "Бул маселе чечилиши керек болгон иш экен. Арген жакында байланышка чыгат! ⏳",
    "Жакшы жаңылык же суроо болсо жазып туруңуз, Арген келгенде сөзсүз окуп жооп берет! ✨",
    "Күтө туруңуз, досум, Арген жакында келип бардык суроолоруңузга жооп берет! 🚀"
]

@bot.business_message_handler(func=lambda message: True)
def handle_business_message(message):
    if not message.text:
        return

    chat_id = message.chat.id
    user_name = message.from_user.first_name or "Досум"
    text = message.text.strip().lower()

    last_message_time[chat_id] = time.time()
    user_replied.discard(chat_id)

    # 1. Эгер колдонуучу эң биринчи жолу жазып жатса гана саламдашуу жана музыка боту тууралуу маалымат жиберет
    if chat_id not in welcomed_users:
        welcomed_users.add(chat_id)
        assistant_text = (
            f"<b>Саламатсызбы, {user_name}!</b> 🔥 Мен Аргендин жеке жардамчы ботумун. ✨\n\n"
            "Эгер маанилүү ишиңиз болсо — келгиле, талкуулайлы. "
            "Ал эми «Аргенди күтөм» десеңиз, аны чакырып беришим мүмкүн! 😍\n\n"
            "🎵 <i>Жана эгер издеген бир ырыңыз же бир видеоңуз болсо, биздин</i> <b>@Tvmmusicbotbotbot</b> <i>ботубузга катталып, тапай жүргөн ыр жана видеолоруңузду өтө мыкты качестводо таба аласыз!</i> 🎧🚀"
        )
        try:
            bot.send_message(
                chat_id=chat_id,
                text=assistant_text,
                parse_mode="HTML",
                reply_to_message_id=message.message_id,
                business_connection_id=message.business_connection_id
            )
        except Exception:
            pass
        return  # Биринчи саламдашуудан кийин токтоп турат, адам кайра жазганда гана төмөнкү код иштейт

    # 2. Адам ар бир кийинки жолу жазганда гана ушул жооптор кайтарылат
    reply_text = random.choice(smart_replies)
    
    if "салам" in text or "алло" in text or "хай" in text:
        reply_text = f"Салам, {user_name}! ✋ Арген азыр бир аз бош эмес болуп жатат, бирок сиздин билдирүүңүздү өткөрүп берем."
    elif "кандай" in text or "чон" in text:
        reply_text = f"Рахмат, баары жакшы! Өзүңүз кандайсыз, {user_name}? Арген келгенде жазып жиберет. 😊"
    elif "арген" in text:
        reply_text = f"Аргенди чакырып жатасызбы? 📳 Мен ага кабар бердим, жакында байланышка чыгат!"

    try:
        bot.send_message(
            chat_id=chat_id,
            text=f"<b>{user_name},</b> {reply_text}",
            parse_mode="HTML",
            business_connection_id=message.business_connection_id
        )
    except Exception:
        pass

    # 3. 30 секунддун ичинде Арген келбесе эскертүү берүү таймери
    def check_and_reply():
        time.sleep(30)
        if chat_id in last_message_time and chat_id not in user_replied:
            try:
                bot.send_message(
                    chat_id=chat_id,
                    text=f"⏳ <b>{user_name},</b> күтө туруңуз, Арген жакында келип жооп берет! 🫡",
                    parse_mode="HTML",
                    business_connection_id=message.business_connection_id
                )
            except:
                pass

    threading.Thread(target=check_and_reply, daemon=True).start()

async def handle(request):
    return web.Response(text="Smart Assistant Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    while True:
        await asyncio.sleep(3600)

def run_web():
    asyncio.run(web_server())

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()

    print("Бот ишке кирди!")
    bot.infinity_polling()
