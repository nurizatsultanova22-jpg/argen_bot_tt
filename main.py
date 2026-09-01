import os
import asyncio
import threading
from datetime import datetime
import telebot
from aiohttp import web

TOKEN = "8387252723:AAGSgqC0yOJ2X-qAcgAIr0WsL7rnjIUyUGc"

bot = telebot.TeleBot(TOKEN)
daily_welcomed_users = {}

def can_send_today(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    if daily_welcomed_users.get(user_id) == today:
        return False
    daily_welcomed_users[user_id] = today
    return True

# 1. Жеке чаттар (Личка) үчүн
@bot.business_message_handler(func=lambda message: True)
def handle_business_message(message):
    if not message.text:
        return

    if getattr(message, 'is_outgoing', False):
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Друг"

    if can_send_today(user_id):
        assistant_text = (
            f"👋 <b>Здравствуйте, {user_name}!</b> Как ваши дела?\n\n"
            "⏳ Арген сейчас занят. Я передам ему ваше сообщение, и он обязательно ответит позже.\n\n"
            "🎵 <i>А пока рекомендуем подписаться на нашего бота</i> <b>@Tvmmusicbotbotbot</b> — "
            "там вы сможете легко находить любые песни и видео из TikTok, YouTube, Instagram и других платформ просто по ссылке! 🚀\n\n"
            "✨ Спасибо, что вы с нами!"
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

# 2. Топтор үчүн (Сизди @mention кылганда же "Арген" дегенде)
@bot.message_handler(func=lambda message: True)
def handle_group_messages(message):
    # Эгер жеке чат болсо өткөрүп жиберебиз (аны жогорку бизнес хендлер карайт)
    if message.chat.type == 'private':
        return

    if not message.text:
        return

    text_lower = message.text.lower()
    
    # "арген" деген сөз же атыңыз жазылганын текшерүү
    if "арген" in text_lower:
        user_id = message.from_user.id
        user_name = message.from_user.first_name or "Друг"

        if can_send_today(user_id):
            group_text = (
                f"⏳ <b>{user_name}</b>, Арген сейчас занят, немного подождите, он сам придет и ответит, прошу прощения.\n\n"
                "🎵 А также загляните в наш музыкальный бот: @Tvmmusicbotbotbot — там можно найти любые песни и видео!"
            )
            try:
                bot.send_message(
                    chat_id=message.chat.id,
                    text=group_text,
                    parse_mode="HTML",
                    reply_to_message_id=message.message_id
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
