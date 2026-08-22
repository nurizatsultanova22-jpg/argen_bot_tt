import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, FSInputFile
import yt_dlp
from datetime import datetime, time

TOKEN = "8942513598:AAEKmhG19rlQDiIKbL9zd-2p0W9iaaDFfxo"
ADMIN_USERNAME = "@Argen_70"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Колдонуучуларга видео 1 жолу гана барышы үчүн сактап турабыз
sent_videos = set()

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Календарь и дата", callback_data="show_calendar"))
    builder.row(InlineKeyboardButton(text="🎬 Посмотреть видео", callback_data="send_video_now"))
    builder.row(InlineKeyboardButton(text="💎 Наша группа", url="https://t.me/taanyshuu_chatyy"))
    builder.row(InlineKeyboardButton(text="⚡️ СВЯЗЬ С АДМИНОМ", url="https://t.me/Argen_70"))
    return builder.as_markup()

# 30 мүнөттөн кийин видеону 1 жолу гана жөнөтүү
async def delayed_video_sender(user_id: int):
    await asyncio.sleep(1800)  # 30 минут
    if user_id not in sent_videos:
        sent_videos.add(user_id)
        video_path = "VID_20260819_112703_701.mp4"
        if os.path.exists(video_path):
            video_file = FSInputFile(video_path)
            try:
                await bot.send_video(
                    chat_id=user_id,
                    video=video_file,
                    caption="✨ Убакыт өтүп, убада кылынган эң сонун видеоңуз келди! Көрүп маанай көтөрүңүз! 🎬🔥",
                    reply_markup=get_main_menu()
                )
            except:
                pass

# Күн сайын эртең менен жана кечинде кабар жиберүүчү фондук процесс
async def daily_scheduler():
    while True:
        now = datetime.now()
        current_time = now.time()
        
        # Эртең мененки кутман таң (саат 07:00 же 08:00 аралыгында бир жолу же саат 07:00 так маалында)
        if current_time.hour == 7 and current_time.minute == 0:
            # Бул жерде активдүү колдонуучуларга же базага жөнөтүү логикасы болот
            # Азырынча мисал катары функция даяр турат
            pass
            
        await asyncio.sleep(60) # Ар бир 1 мүнөт сайын убакытты текшерип турат

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    try:
        await message.answer_sticker("CAACAgIAAxkBAAEL6k1l-gABAAFS1a4AAUo6C0k-AAJ_AAIhx_0rAAGS9-i20eJjNQQ")
    except:
        pass
    
    welcome_text = (
        "✨ **Салам! Жүрөктөн чыккан саламымды кабыл ал!** ✨\n\n"
        "Сени көрүнгөнүнө абдан кубанычтамын. Ботко кош келдиң! 🌸\n\n"
        "Бул жерден каалаган ырыңды эң жогорку сапатта (`320kbps`) издеп таба аласың. "
        "Жөн гана ырдын атын жазып жибер! 🤗🎶\n\n"
        "⏱ *Эскертүү:* Жакынкы убакта сизге атайын белек видео келет!"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())
    
    # Видео үчүн 30 мүнөттүк таймерди иштетебиз (1 жолу гана барат)
    if message.from_user.id not in sent_videos:
        asyncio.create_task(delayed_video_sender(message.from_user.id))

@dp.callback_query(F.data == "show_calendar")
async def show_calendar(callback: types.CallbackQuery):
    now = datetime.now()
    current_time_val = now.time()
    
    # Күн тартибине жараша эртең менен же кечки жылуу сөздөр
    if 6 <= current_time_val.hour < 12:
        greeting = "🌅 **Кутман таң! Күнүңүз ийгиликтүү башталып, жагымдуу болсун!** ✨"
    elif 17 <= current_time_val.hour < 23:
        greeting = "🌙 **Кайырдуу кеч! Күнүңүз жакшы өткөндүр деп үмүттөнөм, эс алыңыз!** ✨"
    else:
        greeting = "🌿 **Күнүңүз абдан маңыздуу жана жемиштүү өтсүн!** ✨"

    current_date = now.strftime("%d.%m.%Y")
    current_time_str = now.strftime("%H:%M")
    
    calendar_text = (
        f"{greeting}\n\n"
        f"📅 **Бүгүнкү календарь жана убакыт:**\n"
        f"🗓 Күнү: **{current_date}**\n"
        f"⏰ Убакыт: **{current_time_str}**\n\n"
        f"Эч качан капа болбоңуз, баары жакшы болот! 🤗"
    )
    await callback.message.answer(calendar_text, parse_mode="Markdown", reply_markup=get_main_menu())
    await callback.answer()

@dp.callback_query(F.data == "send_video_now")
async def send_video_now(callback: types.CallbackQuery):
    video_path = "VID_20260819_112703_701.mp4"
    if os.path.exists(video_path):
        video_file = FSInputFile(video_path)
        await callback.message.answer_video(
            video=video_file,
            caption="🎬 Мына сиз каалаган видео! Керемет маанай каалайм! ✨",
            reply_markup=get_main_menu()
        )
    else:
        await callback.message.answer("⚠️ Видео файлы серверде табылган жок.", reply_markup=get_main_menu())
    await callback.answer()

@dp.message()
async def fallback_search(message: types.Message):
    query = message.text.strip()
    if query.startswith("/"):
        return
    
    # Кечкисин же эртең менен музыка сураганда дароо жылуу каалоо менен кошо жооп беребиз
    waiting_msg = await message.answer("🎧 **Ыр изделүүдө, сабыр кылыңыз...** 🎶", parse_mode="Markdown")
    
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
            await message.answer_audio(
                audio=audio_file, 
                caption=f"✅ **Табылды:** {query} (320kbps)\n✨ Жакшы угуп маанай көтөрүңүз!", 
                parse_mode="Markdown", 
                reply_markup=get_main_menu()
            )
            os.remove(real_file)
        else:
            await message.answer("❌ Тилекке каршы, бул ыр табылган жок. Башка аталышта жазып көрүңүзчү.", parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        await message.answer("⚠️ Серверден ката кетти, кийинчерээк кайра аракет кылып көрүңүз.", parse_mode="Markdown", reply_markup=get_main_menu())
    finally:
        try: await bot.delete_message(message.chat.id, waiting_msg.message_id)
        except: pass

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    # Фондук убакыт текшергичти кошо баштайбыз
    asyncio.create_task(daily_scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
