import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web
import yt_dlp
import os
import random

TOKEN = "8975463458:AAGNJxMQkvkB35XOuGuFU9f1X3ohlABDdBw"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- БАЗА ДАННЫХ ДЛЯ КЭША ---
def init_db():
    conn = sqlite3.connect("bot_cache.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS music_cache (
            query TEXT PRIMARY KEY,
            file_id TEXT,
            title TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_cached_audio(query):
    conn = sqlite3.connect("bot_cache.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, title FROM music_cache WHERE query = ?", (query.lower(),))
    res = cursor.fetchone()
    conn.close()
    return res if res else None

def save_cached_audio(query, file_id, title):
    conn = sqlite3.connect("bot_cache.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO music_cache (query, file_id, title) VALUES (?, ?, ?)", (query.lower(), file_id, title))
    conn.commit()
    conn.close()

# --- КЛАВИАТУРА ---
def get_main_reply_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="💎 Наша группа"),
        KeyboardButton(text="⚡️ Связь с админом")
    )
    return builder.as_markup(resize_keyboard=True)

# --- КОМАНДЫ БОТА ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    try:
        await message.answer_sticker("CAACAgIAAxkBAAEL6k1l-gABAAFS1a4AAUo6C0k-AAJ_AAIhx_0rAAGS9-i20eJjNQQ")
    except:
        pass
    
    welcome_text = (
        "🟢 **Добро пожаловать в музыкальный бот!** 🎧\n\n"
        "Только SoundCloud поиск!\n"
        "Напишите в начале **«Трек [название]»** или **«Найти [название]»**! 🎶"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_reply_menu())

@dp.message(F.text == "💎 Наша группа")
async def btn_group(message: types.Message):
    await message.answer("💎 Группа: https://t.me/taanyshuu_chatyy", reply_markup=get_main_reply_menu())

@dp.message(F.text == "⚡️ Связь с админом")
async def btn_admin(message: types.Message):
    await message.answer("⚡️ Админ: https://t.me/Argen_70", reply_markup=get_main_reply_menu())

# --- ТОЛЬКО SOUNDCLOUD ИЗДӨӨ ЖАНА КЭШ ---
@dp.message()
async def search_music_options(message: types.Message):
    text = message.text.strip()
    if text.startswith("/"):
        return
    
    text_lower = text.lower()
    query = ""
    
    if text_lower.startswith("трек "):
        query = text[5:].strip()
    elif text_lower.startswith("найти "):
        query = text[6:].strip()
    else:
        await message.answer("⚠️ Пожалуйста, напишите запрос начиная со слова **«Трек»** или **«Найти»**.", parse_mode="Markdown", reply_markup=get_main_reply_menu())
        return

    if not query:
        await message.answer("❌ Вы не указали название трека после ключевого слова.", parse_mode="Markdown", reply_markup=get_main_reply_menu())
        return

    cached = get_cached_audio(query)
    if cached:
        file_id, title = cached
        try:
            await message.answer_audio(
                audio=file_id,
                caption=f"💚 **{title}** \n⚡️ Из кэша (мгновенно)",
                parse_mode="Markdown",
                reply_markup=get_main_reply_menu()
            )
            return
        except:
            pass

    waiting_msg = await message.answer("🟢 **Ищем трек в SoundCloud...** 🎧", parse_mode="Markdown")

    filename = f"audio_{random.randint(10000, 99999)}.mp3"
    
    # SoundCloud үчүн гана арналган жөндөөлөр
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": filename,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "noplaylist": True,
        "default_search": "scsearch",
        "socket_timeout": 25,
    }

    track_title = query
    success = False

    try:
        def download_file():
            nonlocal track_title, success
            # SoundCloud издөө форматын тактоого келтирдик
            search_query = f"scsearch:{query}"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=True)
                if info:
                    if "entries" in info and info["entries"]:
                        item = info["entries"][0]
                    else:
                        item = info
                    track_title = item.get("title", query)
                    success = True

        await asyncio.to_thread(download_file)
    except Exception as e:
        print(f"SoundCloud Search/Download error: {e}")

    try:
        await bot.delete_message(message.chat.id, waiting_msg.message_id)
    except:
        pass

    if not success or not os.path.exists(filename):
        await message.answer("❌ В SoundCloud ничего не найдено по вашему запросу.", parse_mode="Markdown", reply_markup=get_main_reply_menu())
        return

    try:
        audio_file = types.FSInputFile(filename)
        sent_msg = await message.answer_audio(
            audio=audio_file,
            caption=f"💚 **{track_title}** \n🔥 SoundCloud аркылуу табылды",
            parse_mode="Markdown",
            reply_markup=get_main_reply_menu()
        )
        
        if sent_msg.audio:
            save_cached_audio(query, sent_msg.audio.file_id, track_title)

    except Exception as e:
        print(f"Send audio error: {e}")
        await message.answer("⚠️ Ошибка при отправке аудиофайла.", parse_mode="Markdown", reply_markup=get_main_reply_menu())

    finally:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

# --- ВЕБ-СЕРВЕР ДЛЯ РЕНДЕРА ---
async def handle(request):
    return web.Response(text="Bot is running smoothly!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
