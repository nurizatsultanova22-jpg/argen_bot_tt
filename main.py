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
from datetime import datetime, timedelta
import random

TOKEN = "8942513598:AAEKmhG19rlQDiIKbL9zd-2p0W9iaaDFfxo"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- БАЗА МЕНЕН ИШТӨӨ ---
def init_db():
    conn = sqlite3.connect("bot_cache.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS music_cache (
            query TEXT PRIMARY KEY,
            file_id TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT UNIQUE,
            caption TEXT,
            created_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_cached_audio(query):
    conn = sqlite3.connect("bot_cache.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id FROM music_cache WHERE query = ?", (query.lower(),))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def save_cached_audio(query, file_id):
    conn = sqlite3.connect("bot_cache.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO music_cache (query, file_id) VALUES (?, ?)", (query.lower(), file_id))
    conn.commit()
    conn.close()

def save_video_to_db(file_id, caption="Видео дня"):
    conn = sqlite3.connect("bot_cache.db")
    cursor = conn.cursor()
    now = datetime.now()
    try:
        cursor.execute("INSERT OR IGNORE INTO videos (file_id, caption, created_at) VALUES (?, ?, ?)", (file_id, caption, now))
        conn.commit()
    except:
        pass
    conn.close()

def get_all_videos():
    conn = sqlite3.connect("bot_cache.db")
    cursor = conn.cursor()
    one_day_ago = datetime.now() - timedelta(days=1)
    cursor.execute("DELETE FROM videos WHERE created_at < ?", (one_day_ago,))
    conn.commit()
    cursor.execute("SELECT file_id, caption FROM videos")
    res = cursor.fetchall()
    conn.close()
    return res

# --- КЛАВИАТУРА ---
def get_main_reply_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📅 Календарь и дата"),
        KeyboardButton(text="🎬 Видео (24ч)")
    )
    builder.row(
        KeyboardButton(text="💬 Теплые слова"),
        KeyboardButton(text="🎲 Интерактив")
    )
    builder.row(
        KeyboardButton(text="💎 Наша группа"),
        KeyboardButton(text="⚡️ Связь с админом")
    )
    return builder.as_markup(resize_keyboard=True)

async def maybe_react(message: types.Message):
    reactions = ["💚", "🎧", "🎶", "✨"]
    if random.random() < 0.3:
        try:
            await message.react([types.ReactionTypeEmoji(emoji=random.choice(reactions))])
        except:
            pass

# --- БОТ КОМАНДАЛАРЫ ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await maybe_react(message)
    try:
        await message.answer_sticker("CAACAgIAAxkBAAEL6k1l-gABAAFS1a4AAUo6C0k-AAJ_AAIhx_0rAAGS9-i20eJjNQQ")
    except:
        pass
    
    welcome_text = (
        "🟢 **Музыкалык Ботко кош келиңиз!** 🎧\n\n"
        "Ыр издөө үчүн каалаган тректин атын жазыңыз. "
        "Бот сизге ырларды таап жана жүктөп берет! 🎶"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_reply_menu())

@dp.message(F.text == "📅 Календарь и дата")
async def btn_calendar(message: types.Message):
    now = datetime.now()
    calendar_text = f"📅 **Күн:** {now.strftime('%d.%m.%Y')} | ⏰ **Убакыт:** {now.strftime('%H:%M')}"
    await message.answer(calendar_text, parse_mode="Markdown", reply_markup=get_main_reply_menu())

@dp.message(F.text == "💬 Теплые слова")
async def btn_warm_words(message: types.Message):
    compliments = [
        "💚 **Бүгүнкү күнүңүз эң сонун маанайда өтсүн!** ✨",
        "🎧 **Музыка менен күнүңүздү жаркын кылыңыз!**",
        "✨ **Сиз ар дайым бийиктиктесиз!** 🔥"
    ]
    await message.answer(random.choice(compliments), parse_mode="Markdown", reply_markup=get_main_reply_menu())

@dp.message(F.text == "🎲 Интерактив")
async def btn_entertainment(message: types.Message):
    await message.answer("💚 **Музыкалык вайб:** Жакшы музыка — жан дүйнөнүн эс алуусу! 🎧", parse_mode="Markdown", reply_markup=get_main_reply_menu())

@dp.message(F.text == "🎬 Видео (24ч)")
async def btn_videos_list(message: types.Message):
    videos = get_all_videos()
    if not videos:
        await message.answer("⚠️ Азырынча видео жок.", reply_markup=get_main_reply_menu())
    else:
        for file_id, caption in videos:
            try:
                await message.answer_video(video=file_id, caption=caption, reply_markup=get_main_reply_menu())
            except:
                pass

@dp.message(F.text == "💎 Наша группа")
async def btn_group(message: types.Message):
    await message.answer("💎 Группа: https://t.me/taanyshuu_chatyy", reply_markup=get_main_reply_menu())

@dp.message(F.text == "⚡️ Связь с админом")
async def btn_admin(message: types.Message):
    await message.answer("⚡️ Админ: https://t.me/Argen_70", reply_markup=get_main_reply_menu())

@dp.message(F.video)
async def handle_incoming_video(message: types.Message):
    save_video_to_db(message.video.file_id, message.caption or "Видео")
    await message.answer("✅ Видео сакталды (24 саатка)!", reply_markup=get_main_reply_menu())

# --- МУЗЫКА ИЗДӨӨ ЖАНА ЖӨНӨТҮҮ ЛОГИКАСЫ ---
@dp.message()
async def search_music_options(message: types.Message):
    text = message.text.strip()
    if text.startswith("/"):
        return
    
    await maybe_react(message)
    
    query = text
    if text.lower().startswith("трек "):
        query = text[5:].strip()
    elif text.lower().startswith("найти "):
        query = text[6:].strip()

    cached_file_id = get_cached_audio(query)
    if cached_file_id:
        await message.answer_audio(
            audio=cached_file_id,
            caption=f"💚 **Табылды (Кэш):** {query} 🔥",
            parse_mode="Markdown",
            reply_markup=get_main_reply_menu()
        )
        return

    waiting_msg = await message.answer("🟢 **Трек изделүүдө...** 🎧", parse_mode="Markdown")

    ydl_opts = {
        "format": "bestaudio",
        "quiet": True,
        "noplaylist": True,
        "default_search": "ytsearch1",
        "socket_timeout": 15,
    }

    audio_url = None
    track_title = query

    try:
        def search_yt():
            nonlocal audio_url, track_title
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query} audio", download=False)
                if info:
                    entries = info.get("entries", [])
                    if entries:
                        item = entries[0]
                        audio_url = item.get("url")
                        track_title = item.get("title", query)

        await asyncio.to_thread(search_yt)

    except Exception as e:
        print(f"Search error: {e}")

    try:
        await bot.delete_message(message.chat.id, waiting_msg.message_id)
    except:
        pass

    if not audio_url:
        await message.answer("❌ Трек табылган жок. Сураныч, башка аталыштагы трек жазып көрүңүз.", parse_mode="Markdown", reply_markup=get_main_reply_menu())
        return

    try:
        sent_msg = await message.answer_audio(
            audio=audio_url,
            caption=f"💚 **{track_title}** \n🔥 Ийгиликтүү табылды!",
            parse_mode="Markdown",
            reply_markup=get_main_reply_menu()
        )
        
        if sent_msg.audio:
            save_cached_audio(query, sent_msg.audio.file_id)

    except Exception as e:
        print(f"Send audio error: {e}")
        await message.answer("⚠️ Аудиону жөнөтүүдө ката кетти.", parse_mode="Markdown", reply_markup=get_main_reply_menu())

# --- RENDER СЕРВЕР ҮЧҮН ВЕБ-ПОРТ (ПИНГ КЫЛУУГО ИЙГИЛИКТҮҮ ИШТЕЙТ) ---
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
