import os
import asyncio
import threading
import time
import telebot
from aiohttp import web

TOKEN = "8387252723:AAGSgqC0yOJ2X-qAcgAIr0WsL7rnjIUyUGc"
bot = telebot.TeleBot(TOKEN)

welcomed_users = set()
last_message_time = {}
user_replied = set()

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if not message.text:
        return

    chat_id = message.chat.id
    user_name = message.from_user.first_name or "Досум"

    last_message_time[chat_id] = time.time()
    user_replied.discard(chat_id)

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
                reply_to_message_id=message.message_id
            )
            
            def check_and_reply():
                time.sleep(30)
                if chat_id in last_message_time and chat_id not in user_replied:
                    try:
                        bot.send_message(
                            chat_id=chat_id,
                            text=f"⏳ <b>{user_name},</b> күтө туруңуз, Арген жакында келип жооп берет! 🫡",
                            parse_mode="HTML"
                        )
                    except:
                        pass

            threading.Thread(target=check_and_reply, daemon=True).start()

        except Exception:
            pass

async def handle(request):
    return web.Response(text="Assistant Bot is running!")

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

    print("Жардамчы бот жаңы токкен менен иштеди!")
    bot.infinity_polling()
