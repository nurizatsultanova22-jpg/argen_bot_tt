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

# --- ТҮЗ ЖАНА ТУРУКТУУ ИЗДӨӨ КОДУ ---
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

    waiting_msg = await message.answer("🟢 **Трек изделүүдө...** 🎧", parse_mode="Markdown")

    # yt-dlp параметрлери (автоматикалык түрдө SoundCloud жана башка ачык булактардан издейт)
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "extract_flat": False,
        "noplaylist": True,
    }

    try:
        def search_tracks():
            # SoundCloud аркылуу издөө префикси туруктуу иштейт
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    results = ydl.extract_info(f"scsearch3:{query}", download=False)
                    if results and "entries" in results:
                        return results["entries"]
                except:
                    pass
                
                # Эгер андан таппаса кадимки жалпы сурам аркылуу текшерет
                try:
                    results = ydl.extract_info(f"auto:{query}", download=False)
                    if results:
                        if "entries" in results:
                            return results["entries"]
                        else:
                            return [results]
                except:
                    pass
                return []

        entries = await asyncio.to_thread(search_tracks)

        if not entries:
            await message.answer("❌ Эч нерсе табылган жок. Башка сөз менен издеп көрүңүз.", parse_mode="Markdown", reply_markup=get_main_reply_menu())
            await bot.delete_message(message.chat.id, waiting_msg.message_id)
            return

        builder = InlineKeyboardBuilder()
        count = 0
        for entry in entries:
            if not entry:
                continue
            title = entry.get("title")
            url = entry.get("webpage_url") or entry.get("url")
            if title and url:
                count += 1
                builder.row(InlineKeyboardButton(text=f"🟢 {count}. {title[:35]}...", callback_data=f"dl_{url[:50]}"))
                # URL толук сакталышы үчүн жекке словарь же кэш колдонсо да болот, бирок айрыкча scsearch үчүн url түздөн-түз келет
            if count >= 3:
                break

        await bot.delete_message(message.chat.id, waiting_msg.message_id)
        
        if builder.buttons:
            # URL'дерди убактылуу сактоо үчүн callback_data узундугу чектелгендиктен, сонун жолун колдонобуз
            # Бирок жөнөкөй тизме үчүн төмөнкүдөй кылабыз:
            pass

        # Ишенимдүү жана түздөн-түз биринчи чыккан тректи автоматтык түрдө жеңил жүктөп берүү же кнопка кылуу:
        # Келгиле, эң биринчи чыккан туура тректи дароо жүктөп берели (ката чыкпас үчүн):
        best_entry = entries[0]
        track_url = best_entry.get("webpage_url") or best_entry.get("url")
        track_title = best_entry.get("title", query)

        await waiting_msg.delete()
        download_msg = await message.answer(f"⏳ **'{track_title[:30]}' жүргүзүлүүдө...** 🎧", parse_mode="Markdown")

        file_prefix = f"audio_{message.from_user.id}_{random.randint(1000,9999)}"
        real_file = f"{file_prefix}.mp3"

        dl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
            "outtmpl": file_prefix,
            "quiet": True,
        }

        def download():
            with yt_dlp.YoutubeDL(dl_opts) as ydl:
                ydl.download([track_url])

        await asyncio.to_thread(download)

        if os.path.exists(real_file):
            audio_file = FSInputFile(real_file, filename="music.mp3")
            sent_msg = await message.answer_audio(
                audio=audio_file,
                caption=f"💚 **{track_title}** \n🔥 Ийгиликтүү жүктөлдү!",
                parse_mode="Markdown",
                reply_markup=get_main_reply_menu()
            )
            if sent_msg.audio:
                save_cached_audio(query, sent_msg.audio.file_id)

            os.remove(real_file)
            await download_msg.delete()
        else:
            await download_msg.edit_text("❌ Тректи жүктөө мүмкүн болбоду.", parse_mode="Markdown", reply_markup=get_main_reply_menu())

    except Exception as e:
        try:
            await bot.delete_message(message.chat.id, waiting_msg.message_id)
        except:
            pass
        await message.answer("⚠️ Ката кетти. Башка трек издеп көрүңүз.", parse_mode="Markdown", reply_markup=get_main_reply_menu())

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
