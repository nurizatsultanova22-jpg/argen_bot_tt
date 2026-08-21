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

# --- ЖӨНДӨӨЛӨР ---
TOKEN = "8942513598:AAEKmhG19rlQDiIKbL9zd-2p0W9iaaDFfxo"
ADMIN_USERNAME = "@Argen_70"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class MusicStates(StatesGroup):
  waiting_for_music_name = State()

# --- МЕНЮ (РУССКИЙ) ---
def get_main_menu():
  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text="🔥 ПОИСК ТРЕКА (SOUNDCLOUD)", callback_data="start_search"))
  builder.row(InlineKeyboardButton(text="⚡️ СУПЕР КНОПКА (Написать админу)", url="https://t.me/Argen_70"))
  builder.row(InlineKeyboardButton(text="💎 Наш канал", url="https://t.me/taanyshuu_chatyy"))
  return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
  await state.clear()
  await message.answer(
      "🥷 **МУЗЫКАЛЬНАЯ БАЗА АРГЕНА** 🥷\n\n"
      "Самый мощный бас и треки в высоком качестве!\n\n"
      "👇 Нажми на кнопку ниже, чтобы начать поиск:",
      parse_mode="Markdown", reply_markup=get_main_menu()
  )

@dp.callback_query(F.data == "start_search")
async def cb_start_search(callback: types.CallbackQuery, state: FSMContext):
  await state.set_state(MusicStates.waiting_for_music_name)
  await callback.message.answer(
      "⚡️ **РЕЖИМ ПОИСКА АКТИВИРОВАН!**\n\n"
      "Напиши в чат: `трек [название]` или `найти [название]`", 
      parse_mode="Markdown"
  )
  await callback.answer()

@dp.message(MusicStates.waiting_for_music_name)
async def process_music_search(message: types.Message, state: FSMContext):
  text = message.text.strip()
  query = ""
  if text.lower().startswith("трек "): query = text[5:].strip()
  elif text.lower().startswith("найти "): query = text[6:].strip()
  else:
      await message.answer("❌ **НЕВЕРНЫЙ ФОРМАТ!** Напиши: `трек [название]`", parse_mode="Markdown")
      return

  waiting_msg = await message.answer("🔥 **ИЩУ ТРЕК (320kbps)...** Подожди немного! ⚡️", parse_mode="Markdown")
  
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
    def download_soundcloud():
      with yt_dlp.YoutubeDL(ydl_opts) as ydl: 
        ydl.download([f"scsearch1:{query}"])
        
    await asyncio.to_thread(download_soundcloud)

    if os.path.exists(real_file):
      audio_file = FSInputFile(real_file, filename=f"{query}.mp3")
      await message.answer_audio(
          audio=audio_file, 
          caption=f"🎧 **НАЙДЕНО: {query}** (320kbps)", 
          parse_mode="Markdown", 
          reply_markup=get_main_menu()
      )
      os.remove(real_file)
    else:
      await message.answer("❌ **ТРЕК НЕ НАЙДЕН!** Попробуй другое название.", parse_mode="Markdown")
  except Exception as e:
      await message.answer("⚠️ **ПРОИЗОШЛА ОШИБКА!** Попробуй еще раз.", parse_mode="Markdown")
      print(f"Error: {e}")
  finally:
      try: await bot.delete_message(chat_id=message.chat.id, message_id=waiting_msg.message_id)
      except: pass
  await state.clear()

async def main():
  await bot.delete_webhook(drop_pending_updates=True)
  await dp.start_polling(bot)

if __name__ == "__main__":
  asyncio.run(main())
