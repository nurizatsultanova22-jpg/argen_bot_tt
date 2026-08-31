import os
import asyncio
import threading
import random
import telebot
from aiohttp import web

TOKEN = "8387252723:AAGSgqC0yOJ2X-qAcgAIr0WsL7rnjIUyUGc"

bot = telebot.TeleBot(TOKEN)
welcomed_users = set()

# Ар кандай маанайдагы жана түрдөгү жооптордун чоң базасы
greetings = [
    "Салам! ✋ Кандай жашоо, кандай иштер?",
    "Саламатсызбы! Келиңиз, кандай маселени талкуулайбыз? ✨",
    "Оо, салам досум! Жакшы жүрөсүңбү? 🚀",
    "Салам! Бүгүнкү күнүңүз кандай өтүп жатат?",
]

how_are_you = [
    "Рахмат, баары тикесинен тик турат! Өзүңүз кандайсыз? 😊",
    "Жаман эмес, шүгүр. Иштер менен алек болуп жатабыз. Сизде жаңылыктар кандай?",
    "Баары сонун! Арген дагы жакында байланышка чыгат.",
]

smart_replies = [
    "Туура айтасыз, бул абдан кызыктуу тема экен! 🤝 Арген келгенде буга токтолобуз.",
    "Бул маселе боюнча ойлонуп көрүш керек экен. Арген өзү окуп чыгып, сөзсүз жооп берет. 💡",
    "Түшүнүктүү! Бул тууралуу кабардар болуп тургула, Арген келип чечип берет.",
    "Мыкты ой экен! Муну Аргенге жеткизип коём, жакында байланышат. 🫡",
    "Кызыктуу суроо же сунуш экен, Арген келгенде чогуу сүйлөшөбүз! ⏳",
    "Макул, маселе катталды. Арген бошоору менен сизге жазып жиберет! ✨",
]

byes = [
    "Анда эмесе азырынча жакшы туруңуз! Жакында байланышабыз. 👋",
    "Макул, аманчылыкта көрүшкөнчө! Иштериңизге ийгилик. 🌟",
]

@bot.business_message_handler(func=lambda message: True)
def handle_business_message(message):
    if not message.text:
        return

    chat_id = message.chat.id
    user_name = message.from_user.first_name or "Досум"
    text = message.text.strip().lower()

    # 1. Биринчи жолу жазганда саламдашуу жана музыка боту тууралуу маалымат жиберет
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
        return

    # 2. Адамдын жазган сөзүнүн маанисине жараша туура жооп тандоо (Адам сыяктуу акылдуу сезим берет)
    if any(word in text for word in ["салам", "хай", "алло", "здарова", "привет"]):
        reply_text = random.choice(greetings)
    elif any(word in text for word in ["кандай", "не жаңылык", "что как", "жизнь"]):
        reply_text = random.choice(how_are_you)
    elif any(word in text for word in ["бай", "көрүшкөнчө", "пока", "рахмат", "саламаттал"]):
        reply_text = random.choice(byes)
    else:
        reply_text = random.choice(smart_replies)

    try:
        bot.send_message(
            chat_id=chat_id,
            text=f"<b>{user_name},</b> {reply_text}",
            parse_mode="HTML",
            business_connection_id=message.business_connection_id
        )
    except Exception:
        pass

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

    print("Акылдуу жана түрдүү сөздүү бот иштеди!")
    bot.infinity_polling()
