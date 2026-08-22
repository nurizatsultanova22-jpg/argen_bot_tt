import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, FSInputFile
import yt_dlp
from datetime import datetime

TOKEN = "8942513598:AAEKmhG19rlQDiIKbL9zd-2p0W9iaaDFfxo"
ADMIN_USERNAME = "@Argen_70"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Календарь и дата", callback_data="show_calendar"))
    builder.row(InlineKeyboardButton(text="💎 Наша группа", url="https://t.me/taanyshuu_chatyy"))
    builder.row(InlineKeyboardButton(text="⚡️ СВЯЗЬ С АДМИНОМ", url="https://t.me/Argen_70"))
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    try:
        await message.answer_sticker("CAACAgIAAxkBAAEL6k1l-gABAAFS1a4AAUo6C0k-AAJ_AAIhx_0rAAGS9-i20eJjNQQ")
    except:
        pass
    
    welcome_text = (
        "✨ **Салам! Кош келдиң!** ✨\n\n"
        "Жүрөгүңө жылуулук, маанайыңа жарыктык каалайм! Сени көрүнгөнүнө абдан кубанычтамын. 🌸\n\n"
        "Бул жерде сен каалаган ырыңды эң жогорку сапатта (`320kbps`) эч кыйынчылыксыз таба аласың. "
        "Жөн гана ырдын же аткаруучунун атын мага жазып жибер, калганын мага тапшыр! 🤗🎶"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

@dp.callback_query(F.data == "show_calendar")
async def show_calendar(callback: types.CallbackQuery):
    now = datetime.now()
    current_date = now.strftime("%d.%m.%Y")
    current_time = now.strftime("%H:%M")
    
    calendar_text = (
        f"📅 **Бүгүнкү календарь жана убакыт:**\n\n"
        f"🗓 Күнү: **{current_date}**\n"
        f"⏰ Убакыт: **{current_time}**\n\n"
        f"🌿 Күнүңүз абдан маңыздуу, жемиштүү жана жагымдуу өтсүн! Эч качан капа болбоңуз, баары жакшы болот! ✨"
    )
    await callback.message.answer(calendar_text, parse_mode="Markdown", reply_markup=get_main_menu())
    await callback.answer()

@dp.message()
async def fallback_search(message: types.Message):
    query = message.text.strip()
    if query.startswith("/"):
        return
    
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
                caption=f"✅ **Табылды:** {query} (320kbps)\n✨ Жакшы угуп көңүл ачыңыз!", 
                parse_mode="Markdown", 
                reply_markup=get_main_menu()
            )
            os.remove(real_file)
        else:
            await message.answer("❌ Тилекке каршы, бул ыр табылган жок. Башка аталышта жазып көрүңүзчү.", parse_mode="Markdown")
    except Exception as e:
        await message.answer("⚠️ Серверден ката кетти, кийинчерээк кайра аракет кылып көрүңүз.", parse_mode="Markdown")
    finally:
        try: await bot.delete_message(message.chat.id, waiting_msg.message_id)
        except: pass

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
