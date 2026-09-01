import os
import asyncio
from datetime import datetime
import telebot
from telebot.async_telebot import AsyncTeleBot
from aiohttp import web

TOKEN = "8990388442:AAF4tO8Gg0aLmRjHaWHp7oKLaCg4PH1O1kc"

bot = AsyncTeleBot(TOKEN)

user_message_counts = {}
replied_chats = set()

@bot.business_message_handler(func=lambda message: True)
async def handle_business_message(message):
    if not message.text:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Друг"
    
    is_outgoing = getattr(message, 'is_outgoing', False)
    if is_outgoing:
        replied_chats.add(chat_id)
        user_message_counts[user_id] = 0
        return

    if chat_id in replied_chats:
        return

    count = user_message_counts.get(user_id, 0) + 1
    user_message_counts[user_id] = count

    # 1-билдирүүгө жооп
    if count == 1:
        text = f"👋 Здравствуйте, {user_name}! Арген сейчас занят, скоро ответит.\n\n🎵 А пока загляните в наш бот: @Tvmmusicbotbotbot"
    
    # 2-билдирүүгө жооп
    elif count == 2:
        text = f"⏳ {user_name}, ваше сообщение передано Аргену. Пожалуйста, немного подождите."
    
    # 3-билдирүүгө жооп
    elif count == 3:
        text = f"⚠️ Арген пока занят на учебе/в делах, но я обязательно напомню ему о вас!"
    
    # 4-билдирүүгө жооп
    elif count == 4:
        text = f"💬 {user_name}, вижу вы пишете много сообщений. Скоро он освободится и всё прочитает."
    
    # 5, 6, 7 жана андан кийинки билдирүүлөргө жооп
    elif count >= 5:
        text = f"🚨 {user_name}, я всё еще на страже! Арген скоро зайдет в сеть и ответит вам лично."
    
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
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

async def main():
    asyncio.create_task(web_server())
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(main())
