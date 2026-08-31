import os
import asyncio
import threading
import time
import telebot
from aiohttp import web
from openai import OpenAI

TOKEN = "8387252723:AAGSgqC0yOJ2X-qAcgAIr0WsL7rnjIUyUGc"
OPENAI_API_KEY = "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"

bot = telebot.TeleBot(TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

welcomed_users = set()
last_message_time = {}
user_replied = set()

@bot.business_message_handler(func=lambda message: True)
def handle_business_message(message):
    if not message.text:
        return

    chat_id = message.chat.id
    user_name = message.from_user.first_name or "Досум"
    text = message.text.strip()

    last_message_time[chat_id] = time.time()
    user_replied.discard(chat_id)

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
        except Exception as e:
            print(f"Welcome error: {e}")

    # 2. OpenAI (ChatGPT) аркылуу адамдын сөзүнө акылдуу жооп кайтаруу
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Сен Арген аттуу жигиттин жеке жардамчы ботусуң. "
                        "Кыргыз тилинде маданияттуу, адам сыяктуу, дос катары кыска жана түшүнүктүү жооп кайтар. "
                        "Эгер маанилүү иши болсо сүйлөшүүгө болорун, ал эми Арген керек болсо чакырып бере аларыңды эскертип тур."
                    )
                },
                {"role": "user", "content": f"Колдонуучунун аты: {user_name}. Айтканы: {text}"}
            ]
        )
        ai_reply = completion.choices[0].message.content

        bot.send_message(
            chat_id=chat_id,
            text=ai_reply,
            parse_mode="HTML",
            business_connection_id=message.business_connection_id
        )
    except Exception as e:
        print(f"OpenAI error: {e}")
        # Эгер OpenAI'де ката кетсе дагы колдонуучу бош калбашы үчүн жөнөкөй жооп жөнөтөбүз
        bot.send_message(
            chat_id=chat_id,
            text=f"{user_name}, сурооңузду кабыл алдым! Арген келип калса жооп берет. 🤝",
            parse_mode="HTML",
            business_connection_id=message.business_connection_id
        )

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
    return web.Response(text="OpenAI Assistant Bot is running!")

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

    print("OpenAI кошулган жардамчы бот иштеди!")
    bot.infinity_polling()
