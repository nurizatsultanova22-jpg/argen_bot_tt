import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, FSInputFile
import yt_dlp
from datetime import datetime, timedelta
import random

TOKEN = "8942513598:AAEKmhG19rlQDiIKbL9zd-2p0W9iaaDFfxo"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

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
        "Бот сизге Yandex Music аркылуу таап берет! 🎶"
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

# --- YANDEX MUSIC АРКЫЛУУ ИЗДӨӨ ---
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
            caption=f"💚 **Табылды (Кэш):** {query} (HQ) 🔥",
            parse_mode="Markdown",
            reply_markup=get_main_reply_menu()
        )
        return

    waiting_msg = await message.answer("🟢 **Тректер изделүүдө (Yandex Music)...** 🎧", parse_mode="Markdown")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "extract_flat": True,
    }

    try:
        def search_tracks():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # yt-dlp yandexmusic search prefix
                results = ydl.extract_info(f"yandexmusicsearch: {query}", download=False)
                return results.get("entries", [])

        entries = await asyncio.to_thread(search_tracks)

        if not entries:
            # Эгер Yandex'тен таппай калса, fallback катары youtube-music издеп көрөбүз
            def fallback_search():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    res = ydl.extract_info(f"ysmsearch3:{query}", download=False)
                    return res.get("entries", [])
            entries = await asyncio.to_thread(fallback_search)

        if not entries:
            await message.answer("❌ Эч нерсе табылган жок.", parse_mode="Markdown", reply_markup=get_main_reply_menu())
            await bot.delete_message(message.chat.id, waiting_msg.message_id)
            return

        builder = InlineKeyboardBuilder()
        for idx, entry in enumerate(entries[:3], 1):
            title = entry.get("title", f"Трек {idx}")
            url = entry.get("url")
            if url:
                builder.row(InlineKeyboardButton(text=f"🟢 Вариант {idx}: {title[:35]}...", callback_data=f"dl_{url}"))

        await bot.delete_message(message.chat.id, waiting_msg.message_id)
        
        if builder.buttons:
            await message.answer(
                f"🟢 **'{query}'** боюнча варианттар табылды:",
                parse_mode="Markdown",
                reply_markup=builder.as_markup()
            )
        else:
            await message.answer("❌ Варианттар табылган жок.", parse_mode="Markdown", reply_markup=get_main_reply_menu())

    except Exception as e:
        try:
            await bot.delete_message(message.chat.id, waiting_msg.message_id)
        except:
            pass
        await message.answer("⚠️ Ката кетти. Башка трек издеп көрүңүз.", parse_mode="Markdown", reply_markup=get_main_reply_menu())

@dp.callback_query(F.data.startswith("dl_"))
async def download_selected_track(callback: types.CallbackQuery):
    track_url = callback.data[3:]
    
    await callback.message.edit_text("⏳ **Жүктөлүүдө...** 🎧", parse_mode="Markdown")

    file_prefix = f"{callback.from_user.id}_{random.randint(1000,9999)}"
    real_file = f"{file_prefix}.mp3"

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}],
        "outtmpl": file_prefix,
        "quiet": True,
    }

    try:
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([track_url])

        await asyncio.to_thread(download)

        if os.path.exists(real_file):
            audio_file = FSInputFile(real_file, filename="music.mp3")
            sent_msg = await callback.message.answer_audio(
                audio=audio_file,
                caption="💚 **Ийгиликтүү жүктөлдү! (320kbps)** 🔥",
                parse_mode="Markdown",
                reply_markup=get_main_reply_menu()
            )
            if sent_msg.audio:
                save_cached_audio(track_url, sent_msg.audio.file_id)

            os.remove(real_file)
            await callback.message.delete()
        else:
            await callback.message.answer("❌ Тректи жүктөө мүмкүн болбоду.", parse_mode="Markdown", reply_markup=get_main_reply_menu())
    except Exception as e:
        await callback.message.answer("⚠️ Жүктөө учурунда ката кетти.", parse_mode="Markdown", reply_markup=get_main_reply_menu())

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
