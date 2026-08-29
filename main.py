import os
import telebot
from yt_dlp import YoutubeDL
from aiohttp import web
import threading

TOKEN = "8797849312:AAEMEvV-WydOdGwElCEzIH44MHpDhvYGmgw"
bot = telebot.TeleBot(TOKEN)

def get_main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("🎵 Ыр издөө үлгүсү"))
    return markup

def get_audio_inline_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🔍 Башканы табуу", callback_data="search_again"),
        telebot.types.InlineKeyboardButton("ℹ️ Маалымат", callback_data="bot_info")
    )
    return markup

@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.text and message.text.lower() in ["start", "башынан"])
def cmd_start(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"<b>Саламатсызбы, {user_name}!</b> ⚡️\n\n"
        "Бул бот ырларды тез арада, күттүрбөй таап берет.\n\n"
        "Ыр издөө үчүн каалаган убакта ырдын атын же <b>трек [аты]</b> деп жазып жибериңиз!"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="HTML", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text and message.text.lower() == "🎵 ыр издөө үлгүсү")
def help_music(message):
    bot.send_message(message.chat.id, "Ыр табуу үчүн мисалы:\n👉 <b>Ок жедим</b> же <b>трек Жамгыр</b> деп жазыңыз.", parse_mode="HTML", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "search_again":
        bot.send_message(call.message.chat.id, "Эми издегиңиз келген ырдын атын жазыңыз:", reply_markup=get_main_keyboard())
        bot.answer_callback_query(call.id)
    elif call.data == "bot_info":
        bot.answer_callback_query(call.id, "⚡️ Бул бот ырларды YouTube платформасынан тез таап берет!", show_alert=True)

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

    wait_msg = bot.send_message(message.chat.id, "⚡️ Изделүүдө...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True
    }

    file_path = None
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            
            title = info.get('title', 'Audio')
            safe_title = "".join([c for c in title if c.isalnum() or c.isspace() or c in "_-"]).strip()
            if not safe_title:
                safe_title = "audio"
            
            mp3_path = f"{safe_title}.mp3"
            filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(filename)
            real_mp3 = base + '.mp3'
            
            if os.path.exists(real_mp3) and real_mp3 != mp3_path:
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)
                os.rename(real_mp3, mp3_path)
            file_path = mp3_path

        if file_path and os.path.exists(file_path):
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
            bot.edit_message_text("❌ Тилекке каршы, бул ыр табылган жок.", message.chat.id, wait_msg.message_id, reply_markup=get_main_keyboard())

    except Exception as e:
        try:
            bot.edit_message_text(f"❌ Ката кетти же ыр табылган жок.", message.chat.id, wait_msg.message_id, reply_markup=get_main_keyboard())
        except:
            pass
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

# Рендер үчүн Web Server (Портту күтүп туруучу)
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
    import asyncio
    asyncio.run(web_server())

if __name__ == "__main__":
    # Веб серверди фондо иштетүү (Render порт талап кылган үчүн)
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()

    print("Ыр табуучу бот ийгиликтүү иштеди!")
    bot.infinity_polling()
