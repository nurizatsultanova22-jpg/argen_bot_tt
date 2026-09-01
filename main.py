import os
import asyncio
from datetime import datetime
import telebot
from telebot.async_telebot import AsyncTeleBot
from aiohttp import web

TOKEN = "8387252723:AAGSgqC0yOJ2X-qAcgAIr0WsL7rnjIUyUGc"

bot = AsyncTeleBot(TOKEN)

# Колдонуучулардын билдирүүлөрүн санап туруу: {user_id: message_count}
user_message_counts = {}
# Арген өзү жооп берген чаттар: set(chat_id)
replied_chats = set()

@bot.business_message_handler(func=lambda message: True)
async def handle_business_message(message):
    if not message.text:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Друг"
    
    # Сиздин өзүңүздүн билдирүүлөрүңүз (outgoing) экенин так текшерүү
    is_outgoing = getattr(message, 'is_outgoing', False)
    if is_outgoing:
        replied_chats.add(chat_id)
        user_message_counts[user_id] = 0
        return

    # Эгер сиз буга чейин жооп берген болсоңуз, бот таптакыр унчукпайт
    if chat_id in replied_chats:
        return

    # Билдирүүлөрдүн санын көбөйтөбүз
    count = user_message_counts.get(user_id, 0) + 1
    user_message_counts[user_id] = count

    # 1. Биринчи билдирүүгө жооп
    if count == 1:
        text_1 = (
            f"👋 <b>Здравствуйте, {user_name}!</b> Как ваши дела?\n\n"
            "⏳ Арген сейчас занят. Я передам ему ваше сообщение, и он обязательно ответит позже.\n\n"
            "🎵 <i>А пока рекомендуем подписаться на нашего бота</i> <b>@Tvmmusicbotbotbot</b> — "
            "там вы сможете легко находить любые песни и видео из TikTok, YouTube, Instagram и других платформ просто по ссылке! 🚀\n\n"
            "✨ Спасибо, что вы с нами!"
        )
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text_1,
                parse_mode="HTML",
                reply_to_message_id=message.message_id,
                business_connection_id=message.business_connection_id
            )
        except Exception:
            pass

    # 2. Үчүнчү билдирүүгө жооп (башкача текст)
    elif count == 3:
        text_3 = (
            f"⚠️ <b>{user_name},</b> я вижу, вы пишете ещё...\n\n"
            "Арген пока всё ещё занят и не успел зайти. Пожалуйста, подождите немного, он обязательно прочитает и ответит вам лично, как только освободится! 🙏"
        )
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text_3,
                parse_mode="HTML",
                reply_to_message_id=message.message_id,
                business_connection_id=message.business_connection_id
            )
        except Exception:
            pass
        user_message_counts[user_id] = 3 

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

async def main():
    await web_server()
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(main())
