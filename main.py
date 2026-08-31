import os
import asyncio
import threading
import telebot
from aiohttp import web

TOKEN = "8387252723:AAGSgqC0yOJ2X-qAcgAIr0WsL7rnjIUyUGc"

bot = telebot.TeleBot(TOKEN)
welcomed_users = set()

@bot.business_message_handler(func=lambda message: True)
def handle_business_message(message):
    if not message.text:
        return

    if getattr(message, 'is_outgoing', False):
        return

    chat_id = message.chat.id
    user_name = message.from_user.first_name or "Друг"

    if chat_id not in welcomed_users:
        welcomed_users.add(chat_id)
        assistant_text = (
            f"<b>Здравствуйте, {user_name}!</b> Как вы?\n\n"
            "Арген пока занят, я передам ему, он сам ответит.\n\n"
            "А также подписывайтесь на нашего бота @Tvmmusicbotbotbot, где вы сможете находить нужные вам песни "
            "и видео из TikTok, YouTube, Instagram и других платформ по ссылке.\n\n"
            "Спасибо за подписку!"
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

async def handle(request):
    return web.Response(text="Bot is running!")

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

    bot.infinity_polling()
