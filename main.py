import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp  # SoundCloud үчүн да yt-dlp эң сонун иштейт!

# --- ЖӨНДӨӨЛӨР ---
TOKEN = "8814386262:AAE8LnwkKaQMVSb96GE_N6VLmQ3Q5RVj2FM"
ADMIN_USERNAME = "@Argen_70"  # Сиздин личкаңыз

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class MusicStates(StatesGroup):
  waiting_for_music_name = State()


# --- ШИКАРНЫЙ МЕНЮ (Старт) ---
def get_main_menu():
  builder = InlineKeyboardBuilder()
  builder.row(
      InlineKeyboardButton(
          text="🔥 ТРЕК ИЗДӨӨ (SOUNDCLOUD)", callback_data="start_search"
      )
  )
  builder.row(
      InlineKeyboardButton(
          text="⚡️ СУПЕР БАСКЫЧ (Админге жазуу)", url=f"https://t.me/Argen_70"
      )
  )
  builder.row(
      InlineKeyboardButton(text="💎 Биздин канал", url="https://t.me/taanyshuu_chatyy")
  )
  return builder.as_markup()


@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
  await state.clear()
  welcome_text = (
      "🥷 **КААНЫШТЫН МУЗЫКАЛЫК БАЗАСЫ** 🥷\n\n"
      "Бул жерде алсыздыкка орун жок! Эң катуу бас, эң агрессивдүү тректер "
      "жана SoundCloud'дун эң сонун жыйнагы чогултулган.\n\n"
      "👇 Төмөнкү баскычты басып издөөнү башта же буйрук бер!"
  )
  await message.answer(
      welcome_text, parse_mode="Markdown", reply_markup=get_main_menu()
  )


# Кнопка аркылуу издөөнү баштоо
@dp.callback_query(F.data == "start_search")
async def cb_start_search(callback: types.CallbackQuery, state: FSMContext):
  await state.set_state(MusicStates.waiting_for_music_name)
  await callback.message.answer(
      "⚡️ **РЕЖИМ АКТИВДЕШТИ!**\n\nТректи табуу үчүн команданы колдон:\n"
      "👉 `трек [ырдын аты]` же `найти [ырдын аты]`\n\nМисалы: "
      "*трек Bakr* же *найти Эндшпиль*",
      parse_mode="Markdown",
  )
  await callback.answer()


# Ырды табуу жана жүктөө (SoundCloud аркылуу туруктуу)
@dp.message(MusicStates.waiting_for_music_name)
async def process_music_search(message: types.Message, state: FSMContext):
  text = message.text.strip()

  # 'трек' же 'найти' сөзү менен башталганын текшерүү
  query = ""
  if text.lower().startswith("трек "):
    query = text[5:].strip()
  elif text.lower().startswith("найти "):
    query = text[6:].strip()
  else:
    await message.answer(
        "❌ **ТУУРА ЭМЕС ФОРМАТ!**\nСөзсүз башына `трек` же `найти` деп жаз!"
        " Жаңыдан аракет кыл.",
        parse_mode="Markdown",
    )
    return

  waiting_msg = await message.answer(
      "🔥 **ТРЕК ИЗДЕЛҮҮДӨ...** База жарылып жатат, күтө тур! ⚡️",
      parse_mode="Markdown",
  )
  real_file = f"{message.from_user.id}_sound.mp3"

  # SoundCloud'дон издөө жөндөөлөрү (эң туруктуу)
  ydl_opts = {
      "format": "bestaudio/best",
      "postprocessors": [{
          "key": "FFmpegExtractAudio",
          "preferredcodec": "mp3",
          "preferredquality": "192",
      }],
      "outtmpl": f"{message.from_user.id}_sound",
      "quiet": True,
      "geo_bypass": True,
  }

  try:

    def download_soundcloud():
      with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # SoundCloud'дон саундтрек издөө
        ydl.download([f"scsearch1:{query}"])

    await asyncio.to_thread(download_soundcloud)

    if os.path.exists(real_file):
      await message.answer_audio(
          audio=types.FSInputFile(real_file),
          caption=(
              f"🎧 **ТАК ТАБЫЛДЫ!**\n🔍 Запрос: `{query}`\n🔥 Стиль:"
              " SoundCloud Aggressive Mode"
          ),
          parse_mode="Markdown",
          reply_markup=get_main_menu(),
      )
      os.remove(real_file)
    else:
      await message.answer(
          "❌ **ТРЕК ТАБЫЛГАН ЖОК!** Башка аталыш менен кайра текшерип көр.",
          parse_mode="Markdown",
      )

  except Exception as e:
    await message.answer(
        "⚠️ **КАТТАЛГАН КАТА!** Сервер кыйналып калды, башка трек жазып көр.",
        parse_mode="Markdown",
    )
    print(f"Error: {e}")

  finally:
    try:
      await bot.delete_message(
          chat_id=message.chat.id, message_id=waiting_msg.message_id
      )
    except:
      pass

  await state.clear()


async def main():
  bot_info = await bot.get_me()
  print("--------------------------------------")
  print(f"🔥 АГРЕССИВДУУ МУЗЫКА БОТУ ИШТЕП БАШТАДЫ!")
  print(f"🤖 Bot Username: @{bot_info.username}")
  print(f"👑 Админ: {ADMIN_USERNAME}")
  print("--------------------------------------")

  await bot.delete_webhook(drop_pending_updates=True)
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main))
