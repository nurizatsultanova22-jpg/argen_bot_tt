import os
import asyncio
import threading
import telebot
from yt_dlp import YoutubeDL
from aiohttp import web

TOKEN = "8797849312:AAEMEvV-WydOdGwElCEzIH44MHpDhvYGmgw"
bot = telebot.TeleBot(TOKEN)

def get_main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("🎵 Пример поиска"))
    return markup

def get_audio_inline_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🔍 Найти другую", callback_data="search_again"),
        telebot.types.InlineKeyboardButton("ℹ️ О боте", callback_data="bot_info")
    )
    return markup

@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.text and message.text.lower() in ["start", "начать", "назад"])
def cmd_start(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"<b>Здравствуйте, {user_name}!</b> ⚡️\n\n"
        "Молниеносный поиск музыки активирован.\n\n"
        "Отправьте название трека!"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="HTML", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text and message.text.lower() == "🎵 пример поиска")
def help_music(message):
    bot.send_message(message.chat.id, "Для точного поиска напишите:\n👉 <b>JONY Камин</b>", parse_mode="HTML", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "search_again":
        bot.send_message(call.message.chat.id, "Введите название следующей песни:", reply_markup=get_main_keyboard())
        bot.answer_callback_query(call.id)
    elif call.data == "bot_info":
        bot.answer_callback_query(call.id, "⚡️ Сверхбыстрый музыкальный бот!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def search_and_send_music(message):
    if not message.text:
        return

    text = message.text.strip()
    if text.lower().startswith("трек "):
        query = text[5:].strip()
    else:
        query = text

    if not query:
        return

    wait_msg = bot.send_message(message.chat.id, "⚡️ 1 секунд...")

    # Так жана эң ылдам издөө жөндөөлөрү
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1',
        'match_filter': lambda info, incomplete: None if info.get('duration', 0) < 60 or info.get('duration', 0) > 600 else None,
        'outtmpl': 'audio_tmp.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android']}}
    }

    file_path = "audio_tmp.mp3"
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            title = info.get('title', 'Audio')

        if os.path.exists(file_path):
            with open(file_path, 'rb') as audio:
                caption_text = f"🎵 <b>{title}</b>\n\n@Argen_70"
                bot.send_audio(
                    message.chat.id, 
                    audio, 
                    caption=caption_text,
                    parse_mode="HTML",
                    reply_markup=get_audio_inline_keyboard()
                )
            try:
                bot.delete_message(message.chat.id, wait_msg.message_id)
            except:
                pass
        else:
            bot.edit_message_text("❌ Трек не найден.", message.chat.id, wait_msg.message_id, reply_markup=get_main_keyboard())

    except Exception:
        try:
            bot.edit_message_text("❌ Ошибка. Напишите точнее.", message.chat.id, wait_msg.message_id, reply_markup=get_main_keyboard())
        except:
            pass
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
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

    print("Бот запущен!")
    bot.infinity_polling()
