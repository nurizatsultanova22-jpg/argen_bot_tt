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

def save_video_to_db(file_id, caption="Бүгүнкү видео"):
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

# --- ТЫКАН ЖАНА ТАРТИПТҮҮ МЕНЮ (АР БИРИ САТЫ МЕНЕН ИЛДЫЙГА) ---
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Календарь и дата", callback_data="show_calendar"))
    builder.row(InlineKeyboardButton(text="🎬 Посмотреть видео (24ч)", callback_data="show_videos_list"))
    builder.row(InlineKeyboardButton(text="💬 Жылуу сөз алуу", callback_data="warm_words"))
    builder.row(InlineKeyboardButton(text="🎲 Зериккенде (Интерактив)", callback_data="fun_entertainment"))
    builder.row(InlineKeyboardButton(text="💎 Наша группа", url="https://t.me/taanyshuu_chatyy"))
    builder.row(InlineKeyboardButton(text="⚡️ СВЯЗЬ С АДМИНОМ", url="https://t.me/Argen_70"))
    return builder.as_markup()

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
        "✨ **Салам! Жүрөктөн чыккан саламымды кабыл ал!** ✨\n\n"
        "Сени көрүнгөнүнө абдан кубанычтамын. Ботко кош келдиң! 🌸\n\n"
        "Бул жерден каалаган ырыңды эң жогорку сапатта (`320kbps`) издеп таба аласың. 🤗🎶"
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

@dp.callback_query(F.data == "warm_words")
async def warm_words(callback: types.CallbackQuery):
    compliments = [
        "💖 **Сиздин жылмаюуңуз башкаларга жарык чачат! Ар дайым күлүп жүрүңүз!** ✨",
        "🌸 **Дүйнөдө сизге окшогон кайталангыс жана жароокер адам бир гана бар!**",
        "✨ **Бүгүнкү күнүңүз укмуштуудай кереметтерге жана ийгиликтерге толсун!** 🔥",
        "🥰 **Кандай гана кыйынчылык болбосун, сиздин күчүңүз бардык нерсеге жетет! Алга!** 🚀",
        "☕️ **Өзүңүзгө кам көрүңүз, сиз бул дүйнөдөгү эң бактылуу көз ирмемдерге татыктуусуз!**"
    ]
    selected_compliment = random.choice(compliments)
    await callback.message.answer(selected_compliment, parse_mode="Markdown", reply_markup=get_main_menu())
    await callback.answer()

@dp.callback_query(F.data == "fun_entertainment")
async def fun_entertainment(callback: types.CallbackQuery):
    fun_texts = [
        "💡 **Билгиңиз келеби?** \nАдам мээси бир күндө орточо 70,000ден ашык ой ойлонот экен!",
        "🌟 **Күндүн мотивациясы:** \nСиз колуңуздан келгенден да артыкка татыктуусуз! Бүгүн эң сонун күн болот! 🔥",
        "☕️ **Чакан кеңеш:** \nБир чыны жылуу чай ичип, терең дем алып, жарым саатка эс алып алыңыз.",
        "🎨 **Кызыктуу факт:** \nДүйнөдө эң бактылуу адамдар — айланасындагыларга ар дайым жакшы маанай тартуулагандар.",
        "🚀 **Ийгилик сыры:** \nЭч качан башталган иштен коркпоңуз, кичинекей кадамдар чоң жеңиштерге алып келет!"
    ]
    selected_text = random.choice(fun_texts)
    await callback.message.answer(f"🎲 **Зеригүүнү жоюу борбору:**\n\n{selected_text}", parse_mode="Markdown", reply_markup=get_main_menu())
    await callback.answer()

@dp.callback_query(F.data == "show_videos_list")
async def show_videos_list(callback: types.CallbackQuery):
    videos = get_all_videos()
    if not videos:
        await callback.message.answer("⚠️ Учурда бүгүнкү видеолор жок. Ботко видео жөнөтсөңүз, ал 24 саат сакталат!", reply_markup=get_main_menu())
    else:
        for file_id, caption in videos:
            try:
                await callback.message.answer_video(video=file_id, caption=caption or "🎬 Бүгүнкү видео", reply_markup=get_main_menu())
            except:
                pass
    await callback.answer()

@dp.message(F.video)
async def handle_incoming_video(message: types.Message):
    file_id = message.video.file_id
    caption = message.caption or "Бүгүнкү видео"
    save_video_to_db(file_id, caption)
    await message.answer("✅ **Видео ийгиликтүү сакталды!** Ботто так **24 саат** сакталып турат.", parse_mode="Markdown", reply_markup=get_main_menu())

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
            caption=f"⚡️ **Табылды (Кэш):** {query} (320kbps) 🔥",
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
