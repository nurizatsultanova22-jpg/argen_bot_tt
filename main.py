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

# --- ЫЛДЫЙГАКЫ КНОПКАЛАР (REPLY KEYBOARD) ---
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
        "✨ **Привет! Добро пожаловать в бот!** ✨\n\n"
        "Здесь вы можете найти любую музыку в самом высоком качестве (`320kbps`). "
        "Просто напишите название песни или отправьте видео! 🤗🎶"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_reply_menu())

# --- ЫЛДЫЙГАКЫ КНОПКАЛАРДЫН ИШТЕШИ ---

@dp.message(F.text == "📅 Календарь и дата")
async def btn_calendar(message: types.Message):
    now = datetime.now()
    current_date = now.strftime("%d.%m.%Y")
    current_time_str = now.strftime("%H:%M")
    
    calendar_text = (
        f"📅 **Текущая дата и время:**\n"
        f"🗓 Дата: **{current_date}**\n"
        f"⏰ Время: **{current_time_str}**\n\n"
        f"🌿 Желаю вам прекрасного и продуктивного дня! ✨"
    )
    await message.answer(calendar_text, parse_mode="Markdown", reply_markup=get_main_reply_menu())

@dp.message(F.text == "💬 Теплые слова")
async def btn_warm_words(message: types.Message):
    compliments = [
        "💖 **Ваша улыбка озаряет всё вокруг! Всегда улыбайтесь!** ✨",
        "🌸 **В этом мире вы — абсолютно уникальный и прекрасный человек!**",
        "✨ **Пусть сегодняшний день принесет вам невероятные чудеса и успехи!** 🔥",
        "🥰 **Какие бы трудности ни были, вашей силы хватит на всё! Вперед!** 🚀",
        "☕️ **Позаботьтесь о себе, вы заслуживаете самых счастливых моментов!**"
    ]
    await message.answer(random.choice(compliments), parse_mode="Markdown", reply_markup=get_main_reply_menu())

@dp.message(F.text == "🎲 Интерактив")
async def btn_entertainment(message: types.Message):
    fun_texts = [
        "💡 **Интересный факт:** \nЧеловеческий мозг за день производит более 70 000 мыслей!",
        "🌟 **Мотивация дня:** \nВы способны на гораздо большее, чем думаете! Сегодня отличный день! 🔥",
        "☕️ **Мини-совет:** \nВыпейте чашечку теплого чая, сделайте глубокий вдох и немного отдохните.",
        "🎨 **Факт:** \nСамые счастливые люди — те, кто дарит окружающим хорошее настроение.",
        "🚀 **Секрет успеха:** \nНикогда не бойтесь начинать, маленькие шаги ведут к великим победам!"
    ]
    await message.answer(f"🎲 **Центр развлечений:**\n\n{random.choice(fun_texts)}", parse_mode="Markdown", reply_markup=get_main_reply_menu())

@dp.message(F.text == "🎬 Видео (24ч)")
async def btn_videos_list(message: types.Message):
    videos = get_all_videos()
    if not videos:
        await message.answer("⚠️ На данный момент видео нет. Отправьте видео в бот, и оно сохранится на 24 часа!", reply_markup=get_main_reply_menu())
    else:
        for file_id, caption in videos:
            try:
                await message.answer_video(video=file_id, caption=caption or "🎬 Видео дня", reply_markup=get_main_reply_menu())
            except:
                pass

@dp.message(F.text == "💎 Наша группа")
async def btn_group(message: types.Message):
    await message.answer("💎 Наша группа: https://t.me/taanyshuu_chatyy", reply_markup=get_main_reply_menu())

@dp.message(F.text == "⚡️ Связь с админом")
async def btn_admin(message: types.Message):
    await message.answer("⚡️ Связь с администратором: https://t.me/Argen_70", reply_markup=get_main_reply_menu())

@dp.message(F.video)
async def handle_incoming_video(message: types.Message):
    file_id = message.video.file_id
    caption = message.caption or "Видео дня"
    save_video_to_db(file_id, caption)
    await message.answer("✅ **Видео успешно сохранено!** Оно будет доступно в боте ровно **24 часа**.", parse_mode="Markdown", reply_markup=get_main_reply_menu())

@dp.message()
async def fallback_search(message: types.Message):
    query = message.text.strip()
    if query.startswith("/"):
        return
    
    await maybe_react(message)
    
    cached_file_id = get_cached_audio(query)
    if cached_file_id:
        await message.answer_audio(
            audio=cached_file_id,
            caption=f"⚡️ **Найдено (Кэш):** {query} (320kbps) 🔥",
            parse_mode="Markdown",
            reply_markup=get_main_reply_menu()
        )
        return

    waiting_msg = await message.answer("🎧 **Поиск музыки, пожалуйста, подождите...** 🎶", parse_mode="Markdown")
    
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
                caption=f"✅ **Найдено:** {query} (320kbps)\n✨ Приятного прослушивания!", 
                parse_mode="Markdown", 
                reply_markup=get_main_reply_menu()
            )
            if sent_msg.audio:
                save_cached_audio(query, sent_msg.audio.file_id)
                
            os.remove(real_file)
        else:
            await message.answer("❌ К сожалению, эта песня не найдена.", parse_mode="Markdown", reply_markup=get_main_reply_menu())
    except Exception as e:
        await message.answer("⚠️ Произошла ошибка сервера, попробуйте позже.", parse_mode="Markdown", reply_markup=get_main_reply_menu())
    finally:
        try: await bot.delete_message(message.chat.id, waiting_msg.message_id)
        except: pass

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
