import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, FSInputFile
import yt_dlp
from datetime import datetime
import random

TOKEN = "8942513598:AAEKmhG19rlQDiIKbL9zd-2p0W9iaaDFfxo"
ADMIN_USERNAME = "@Argen_70"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- БАЗА ДАННЫХ ЖАНА КЭШ ---
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
            file_id TEXT,
            caption TEXT
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

def get_all_videos():
    conn = sqlite3.connect("bot_cache.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, caption FROM videos")
    res = cursor.fetchall()
    conn.close()
    return res

# --- МЕНЮ ---
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Календарь и дата", callback_data="show_calendar"))
    builder.row(InlineKeyboardButton(text="🎬 Посмотреть видео", callback_data="show_videos_list"))
    builder.row(InlineKeyboardButton(text="💎 Наша группа", url="https://t.me/taanyshuu_chatyy"))
    builder.row(InlineKeyboardButton(text="⚡️ СВЯЗЬ С АДМИНОМ", url="https://t.me/Argen_70"))
    return builder.as_markup()

# --- КАНДАЙ БИР РЕАКЦИЯЛАР ---
async def maybe_react(message: types.Message):
    # Кээде (мисалы 30% учурда) билдирүүлөргө автоматтык реакция калтырат
    reactions = ["🔥", "❤️", "👍", "✨", "🥰"]
    if random.random() < 0.3:
        try:
            await message.react([types.ReactionTypeEmoji(emoji=random.choice(reactions))])
        except:
            pass

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await maybe_react(message)
    
    try:
        await message.answer_sticker("CAACAgIAAxkBAAEL6k1l-gABAAFS1a4AAUo6C0k-AAJ_AAIhx_0rAAGS9-i20eJjNQQ")
    except:
        pass
    
    welcome_text = (
        "✨ **Салам! Жүрөктөн чыккан саламымды кабыл ал!** ✨\n\n"
        "Сени көрүнгөнүнө абдан кубанычтамын. Ботко кош келдиң! 🌸\n\n"
        "Бул жерден каалаган ырыңды эң жогорку сапатта (`320kbps`) издеп таба аласың. "
        "Базада бар болсо — **көз ирмемде** таап берет! 🤗🎶"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

@dp.callback_query(F.data == "show_calendar")
async def show_calendar(callback: types.CallbackQuery):
    now = datetime.now()
    current_date = now.strftime("%d.%m.%Y")
    current_time_str = now.strftime("%H:%M")
    
    calendar_text = (
        f"📅 **Бүгүнкү календарь жана убакыт:**\n"
        f"🗓 Күнү: **{current_date}**\n"
        f"⏰ Убакыт: **{current_time_str}**\n\n"
        f"🌿 Күнүңүз абдан маңыздуу, жемиштүү жана жагымдуу өтсүн! ✨"
    )
    await callback.message.answer(calendar_text, parse_mode="Markdown", reply_markup=get_main_menu())
    await callback.answer()

@dp.callback_query(F.data == "show_videos_list")
async def show_videos_list(callback: types.CallbackQuery):
    videos = get_all_videos()
    if not videos:
        # Эгер базада видео жок болсо, демейдеги файлды кошуп жиберебиз дагы көрсөтөбүз
        video_path = "VID_20260819_112703_701.mp4"
        if os.path.exists(video_path):
            sent = await callback.message.answer_video(
                video=FSInputFile(video_path),
                caption="🎬 **Күн сайын жаңыртылуучу видео галерея!** ✨",
                reply_markup=get_main_menu()
            )
            # Базага автоматтык түрдө сактап коёбуз
            conn = sqlite3.connect("bot_cache.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO videos (file_id, caption) VALUES (?, ?)", (sent.video.file_id, "Главное видео"))
            conn.commit()
            conn.close()
        else:
            await callback.message.answer("⚠️ Учурда видеолор жүктөлө элек.", reply_markup=get_main_menu())
    else:
        # Базадагы видеолорду жөнөтүү
        for file_id, caption in videos:
            await callback.message.answer_video(video=file_id, caption=caption or "🎬 Видео", reply_markup=get_main_menu())
    await callback.answer()

@dp.message()
async def fallback_search(message: types.Message):
    query = message.text.strip()
    if query.startswith("/"):
        return
    
    await maybe_react(message)
    
    # 1. Алгач КЭШтен (базадан) издейбиз
    cached_file_id = get_cached_audio(query)
    if cached_file_id:
        await message.answer_audio(
            audio=cached_file_id,
            caption=f"⚡️ **Табылды (Базадан/Кэш):** {query} (320kbps) 🔥",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        return

    waiting_msg = await message.answer("🎧 **Ыр тездик менен изделүүдө...** 🎶", parse_mode="Markdown")
    
    file_prefix = f"{message.from_user.id}_music"
    real_file = f"{file_prefix}.mp3"
    
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}],
        "outtmpl": file_prefix,
        "quiet": True,
        "geo_bypass": True,
    }

    try:
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: 
                ydl.download([f"scsearch1:{query}"])
        await asyncio.to_thread(download)

        if os.path.exists(real_file):
            audio_file = FSInputFile(real_file, filename=f"{query}.mp3")
            sent_msg = await message.answer_audio(
                audio=audio_file, 
                caption=f"✅ **Табылды:** {query} (320kbps)\n✨ Жакшы угуп маанай көтөрүңүз!", 
                parse_mode="Markdown", 
                reply_markup=get_main_menu()
            )
            # Келечекте тез табуу үчүн базага file_id сактап коёбуз
            if sent_msg.audio:
                save_cached_audio(query, sent_msg.audio.file_id)
                
            os.remove(real_file)
        else:
            await message.answer("❌ Тилекке каршы, бул ыр табылган жок.", parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        await message.answer("⚠️ Серверден ката кетти, кайра аракет кылыңыз.", parse_mode="Markdown", reply_markup=get_main_menu())
    finally:
        try: await bot.delete_message(message.chat.id, waiting_msg.message_id)
        except: pass

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
