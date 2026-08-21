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

TOKEN = "8942513598:AAEKmhG19rlQDiIKbL9zd-2p0W9iaaDFfxo"
ADMIN_USERNAME = "@Argen_70"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class MusicStates(StatesGroup):
    waiting_for_music_name = State()

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔥 ПОИСК ТРЕКА (SOUNDCLOUD)", callback_data="start_search"))
    builder.row(InlineKeyboardButton(text="💎 Наша группа", url="https://t.me/taanyshuu_chatyy"))
    builder.row(InlineKeyboardButton(text="⚡️ СВЯЗЬ С АДМИНОМ", url="https://t.me/Argen_70"))
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    # Жылуу маанай жана стикер
    try:
        await message.answer_sticker("CAACAgIAAxkBAAEL6k1l-gABAAFS1a4AAUo6C0k-AAJ_AAIhx_0rAAGS9-i20eJjNQQ")
    except:
        pass
    await message.answer(
        "✨ **Привет! Добро пожаловать!** ✨\n\n"
        "Я твой музыкальный бот. Нажми кнопку ниже или просто отправь название песни, и я найду её в самом лучшем качестве (320kbps) специально для тебя! 😊",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

@dp.callback_query(F.data == "start_search")
async def cb_start_search(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(MusicStates.waiting_for_music_name)
    await callback.message.answer("🎵 **Напиши название песни или исполнителя:**", parse_mode="Markdown")
    await callback.answer()

@dp.message(MusicStates.waiting_for_music_name)
async def process_music_search(message: types.Message, state: FSMContext):
    query = message.text.strip()
    waiting_msg = await message.answer("🎧 **Ищу самый сочный звук (320kbps)...** 🔥", parse_mode="Markdown")
    
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
                caption=f"✅ **Найдено: {query}** (320kbps)", 
                parse_mode="Markdown", 
                reply_markup=get_main_menu()
            )
            os.remove(real_file)
        else:
            await message.answer("❌ Трек не найден. Попробуй другое название.", parse_mode="Markdown")
    except Exception as e:
        await message.answer("⚠️ Ошибка сервера. Попробуй еще раз.", parse_mode="Markdown")
        print(f"Error: {e}")
    finally:
        try: await bot.delete_message(message.chat.id, waiting_msg.message_id)
        except: pass
    await state.clear()

@dp.message()
async def fallback_search(message: types.Message):
    # Эгер состояние күтпөй туруп эле каалаган маалда ыр жазса дагы таап бере турган функция
    query = message.text.strip()
    if query.startswith("/"):
        return
    
    waiting_msg = await message.answer("🎧 **Ищу трек (320kbps)...** 🔥", parse_mode="Markdown")
    
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
                caption=f"✅ **Найдено: {query}** (320kbps)", 
                parse_mode="Markdown", 
                reply_markup=get_main_menu()
            )
            os.remove(real_file)
        else:
            await message.answer("❌ Трек не найден.", parse_mode="Markdown")
    except Exception as e:
        await message.answer("⚠️ Ошибка сервера.", parse_mode="Markdown")
    finally:
        try: await bot.delete_message(message.chat.id, waiting_msg.message_id)
        except: pass

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
