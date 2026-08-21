import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import yt_dlp

# --- ЖӨНДӨӨЛӨР ---
TOKEN = "8814386262:AAE8LnwkKaQMVSb96GE_N6VLmQ3Q5RVj2FM"  # Сенин токениң

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Состояниелер
class MusicSearch(StatesGroup):
  waiting_for_query = State()


# /start командасы
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
  await state.set_state(MusicSearch.waiting_for_query)
  await message.answer(
      "🎵 Салам! Музыкалык ботко кош келиңиз.\n\nМага каалаган ырдын атын же"
      " аткаруучусун жазып жибериңиз (мисалы: *Bakr* же *Камин*), мен аны MP3"
      " форматында таап беремин!",
      parse_mode="Markdown",
  )


# Ырдын атын кабыл алып, издөө жана жүктөө
@dp.message(MusicSearch.waiting_for_query)
async def search_and_send_music(message: types.Message, state: FSMContext):
  query = message.text
  waiting_msg = await message.answer(
      "🔍 Ыр изделүүдө жана даярдалууда, бир аз күтө туруңуз..."
  )

  real_file = f"{message.from_user.id}_music.mp3"

  # YouTube бөгөтүн айланып өтүүчү жөндөөлөр
  ydl_opts = {
      "format": "bestaudio/best",
      "postprocessors": [{
          "key": "FFmpegExtractAudio",
          "preferredcodec": "mp3",
          "preferredquality": "192",
      }],
      "outtmpl": f"{message.from_user.id}_music",
      "quiet": True,
      "geo_bypass": True,
      "nocheckcertificate": True,
      "http_headers": {
          "User-Agent": (
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
              " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
          )
      },
  }

  try:

    def download():
      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch1:{query}"])

    await asyncio.to_thread(download)

    if os.path.exists(real_file):
      await message.answer_audio(
          audio=types.FSInputFile(real_file),
          caption=f"🎧 Табылды: {query}\n🤖 Бот аркылуу жүктөлдү",
      )
      os.remove(real_file)
    else:
      await message.answer(
          "❌ Тилекке каршы, бул ырды таба албадым же жүктөп бере алган жокмун."
      )

  except Exception as e:
    await message.answer(
        "❌ Ката кетти. Башка ырдын атын жазып көрүңүз же кийинрээк"
        " аракет кылыңыз."
    )
    print(f"Error: {e}")

  finally:
    try:
      await bot.delete_message(
          chat_id=message.chat.id, message_id=waiting_msg.message_id
      )
    except:
      pass

  await message.answer("Дагы ыр издегиң келсе, атын жаз:")


async def main():
  bot_info = await bot.get_me()
  print("--------------------------------------")
  print(f"🎵 Музыкалык бот ийгиликтүү иштеди!")
  print(f"🤖 Bot Username: @{bot_info.username}")
  print("--------------------------------------")

  await bot.delete_webhook(drop_pending_updates=True)
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
