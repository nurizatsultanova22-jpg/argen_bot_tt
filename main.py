import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from yt_dlp import YoutubeDL
from aiohttp import web

TOKEN = "8797849312:AAEMEvV-WydOdGwElCEzIH44MHpDhvYGmgw"
ADMIN_ID = 7978591176

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="🎵 Ыр издөө үлгүсү"))
    return builder.as_markup(resize_keyboard=True)

def get_audio_inline_keyboard(query: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🔍 Башканы табуу", callback_data="search_again"),
        types.InlineKeyboardButton(text="ℹ️ Маалымат", callback_data="bot_info")
    )
    return builder.as_markup()

@dp.message(F.text.casefold().in_(["/start", "start", "башынан"]))
async def cmd_start(message: types.Message):
    user = message.from_user
    user_name = user.full_name
    
    welcome_text = (
        f"<b>Саламатсызбы, {user_name}!</b> ⚡️\n\n"
        "Бул бот ырларды тез арада, күттүрбөй таап берет.\n\n"
        "Ыр издөө үчүн каалаган убакта ырдын атын же <b>трек [аты]</b> деп жазып жибериңиз!"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@dp.message(F.text.casefold() == "🎵 ыр издөө үлгүсү")
async def help_music(message: types.Message):
    await message.answer("Ыр табуу үчүн мисалы:\n👉 <b>Ок жедим</b> же <b>трек Жамгыр</b> деп жазыңыз.", parse_mode="HTML", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "search_again")
async def callback_search_again(callback: types.CallbackQuery):
    await callback.message.answer("Эми издегиңиз келген ырдын атын жазыңыз:", reply_markup=get_main_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "bot_info")
async def callback_bot_info(callback: types.CallbackQuery):
    await callback.answer("⚡️ Бул бот ырларды YouTube жана башка платформалардан автоматтык түрдө тез таап берет!", show_alert=True)

# --- ЫРДЫ ТЕЗ ТАБУУ ЖАНА ЖӨНӨТҮҮ ---
@dp.message()
async def search_and_send_music(message: types.Message):
    if not message.text:
        return

    text = message.text.strip()
    
    if text.lower().startswith("трек "):
        query = text[5:].strip()
    else:
        query = text

    if not query:
        return

    wait_msg = await message.answer("⚡️ Изделүүдө...")

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
        def download():
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

                return title, mp3_path

        loop = asyncio.get_running_loop()
        title, file_path = await loop.run_in_executor(None, download)

        if file_path and os.path.exists(file_path):
            audio_file = types.FSInputFile(file_path, filename=f"{title}.mp3")
            caption_text = f"🎵 <b>{title}</b>\n\n@Argen_70"
            
            await message.answer_audio(
                audio=audio_file, 
                caption=caption_text,
                parse_mode="HTML",
                reply_markup=get_audio_inline_keyboard(query)
            )
        else:
            await wait_msg.text = "❌ Тилекке каршы, бул ыр табылган жок."
            await wait_msg.edit_text("❌ Тилекке каршы, бул ыр табылган жок.", reply_markup=get_main_keyboard())
            return
        
        try:
            await wait_msg.delete()
        except Exception:
            pass

    except Exception:
        try:
            await wait_msg.edit_text("❌ Ката кетти же ыр табылган жок. Башка сөз менен издеп көрүңүз.", reply_markup=get_main_keyboard())
        except Exception:
            pass
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

# Рендер үчүн веб-сервер (портту талап кылат)
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
    print("Ыр табуучу бот ийгиликтүү иштеди!")
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
