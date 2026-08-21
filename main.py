import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- ЖӨНДӨӨЛӨР ---
TOKEN = "8814386262:AAE8LnwkKaQMVSb96GE_N6VLmQ3Q5RVj2FM"  # Сенин токениң
CHANNEL_LINK = "https://t.me/taanyshuu_chatyy"  # Таанышуу чатыңдын шилтемеси
CHANNEL_USERNAME = "@taanyshuu_chatyy"  # Чатыңдын аты
# ----------------

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# --- СОСТОЯНИЕ БАШКАРУУ ---
class AnonymousStates(StatesGroup):
  waiting_for_message = State()


# --- БАШКЫ МЕНЮ БАСКЫЧТАРЫ ---
def get_main_menu(my_user_id):
  builder = InlineKeyboardBuilder()
  builder.row(
      InlineKeyboardButton(
          text="📩 Менин шилтемемди алуу", callback_data=f"get_link_{my_user_id}"
      ),
      InlineKeyboardButton(text="📢 Таанышуу чат", url=CHANNEL_LINK),
  )
  return builder.as_markup()


# --- БАШКЫ СТАРТ КОМАНДАСЫ ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
  await state.clear()
  args = message.text.split()

  # Эгер кимдир бирөөнүн жеке шилтемеси аркылуу кирсе (башкага кат жазуу үчүн)
  if len(args) > 1:
    target_id = args[1]
    # Өзүнө-өзү жазганды алдын алуу
    if int(target_id) == message.from_user.id:
      await message.answer(
          "⚠️ Өзүңүзгө анонимдүү кат жаза албайсыз!\n\nБашкаларга жөнөтүү"
          f" үчүн өзүңүздүн шилтемеңизди алыңыз:",
          reply_markup=get_main_menu(message.from_user.id),
      )
      return

    await state.update_data(target_id=target_id)

    ad_text = (
        "🤫 **Анонимдүү билдирүү режими!**\n\nБул адамга жашыруун кат, суроо"
        " же каалаган нерсеңди жаз.\nАл сенин ким экениңди эч качан"
        " билбейт! 🥷\n\n👇 Жана дагы биздин таанышуу чатыбызга кошулуңуз!"
    )

    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📢 Таанышуу чатка кошулуу", url=CHANNEL_LINK)
    )

    await message.answer(
        ad_text, parse_mode="Markdown", reply_markup=builder.as_markup()
    )
    await message.answer(
        "✍️ **Билдирүүнү жазыңыз же жөнөтүңүз** (текст, сүрөт, видео, стикер"
        " ж.б.):"
    )
    await state.set_state(AnonymousStates.waiting_for_message)

  else:
    # Ботту өзү ачып же /start баскандар үчүн меню
    bot_info = await bot.get_me()
    my_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"

    welcome_text = (
        f"👋 Салам! Бул **Анонимдүү билдирүүлөр боту**.\n\nТаанышуу чатыбыз:"
        f" {CHANNEL_USERNAME}\n\nДосторуңа жөнөтүү үчүн өзүңдүн жеке"
        f" шилтемең:\n`{my_link}`\n\nШилтемени көчүрүп, Инстаграмга, TikTok'ко"
        " же Telegram'га ташта. Сага баары анонимдүү кат жаза алышат!"
    )

    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu(message.from_user.id),
    )


# --- КАЛБЭКК ШИЛТЕМЕНИ БЕРҮҮ ---
@dp.callback_query(F.data.startswith("get_link_"))
async def callback_get_link(callback: types.CallbackQuery):
  user_id = callback.data.split("_")[2]
  bot_info = await bot.get_me()
  my_link = f"https://t.me/{bot_info.username}?start={user_id}"

  await callback.message.answer(
      "✅ **Сиздин жеке анонимдүү шилтемеңиз:**\n"
      f"`{my_link}`\n\n"
      "Бул шилтемени көчүрүп соц-тармактарга бөлүшүңүз!",
      parse_mode="Markdown",
  )
  await callback.answer()


# --- ЖОӨП БЕРҮҮ БАСКЫЧЫН ТҮЗҮҮ ---
def get_reply_button(original_sender_id):
  builder = InlineKeyboardBuilder()
  builder.add(
      InlineKeyboardButton(
          text="↩️ Анонимдүү жооп берүү",
          callback_data=f"reply_to_{original_sender_id}",
      )
  )
  return builder.as_markup()


# --- БИЛДИРҮҮНҮ КАБЫЛ АЛЫП, ЭЭСИНЕ ЖӨНӨТҮҮ (МЕДИА ЖАНА ТЕКСТ) ---
@dp.message(AnonymousStates.waiting_for_message)
async def handle_all_anonymous_media(message: types.Message, state: FSMContext):
  data = await state.get_data()
  target_id = data.get("target_id")

  if target_id:
    try:
      original_sender_id = message.from_user.id
      sent_message = None

      if message.text:
        sent_message = await bot.send_message(
            chat_id=int(target_id),
            text=(
                "📩 **Сизге жаңы анонимдүү билдирүү келди:**\n\n"
                f"{message.text}"
            ),
            parse_mode="Markdown",
            reply_markup=get_reply_button(original_sender_id),
        )
      elif message.photo:
        sent_message = await bot.send_photo(
            chat_id=int(target_id),
            photo=message.photo[-1].file_id,
            caption=(
                "📩 **Сизге жаңы анонимдүү сүрөт келди:**\n"
                f"{message.caption or ''}"
            ),
            parse_mode="Markdown",
            reply_markup=get_reply_button(original_sender_id),
        )
      elif message.video:
        sent_message = await bot.send_video(
            chat_id=int(target_id),
            video=message.video.file_id,
            caption=(
                "📩 **Сизге жаңы анонимдүү видео келди:**\n"
                f"{message.caption or ''}"
            ),
            parse_mode="Markdown",
            reply_markup=get_reply_button(original_sender_id),
        )
      elif message.voice:
        sent_message = await bot.send_voice(
            chat_id=int(target_id),
            voice=message.voice.file_id,
            caption="📩 **Сизге жаңы анонимдүү үн билдирүү келди:**",
            parse_mode="Markdown",
            reply_markup=get_reply_button(original_sender_id),
        )
      elif message.sticker:
        sent_message = await bot.send_sticker(
            chat_id=int(target_id),
            sticker=message.sticker.file_id,
            reply_markup=get_reply_button(original_sender_id),
        )
      elif message.document:
        sent_message = await bot.send_document(
            chat_id=int(target_id),
            document=message.document.file_id,
            caption=(
                "📩 **Сизге жаңы анонимдүү файл келди:**\n"
                f"{message.caption or ''}"
            ),
            parse_mode="Markdown",
            reply_markup=get_reply_button(original_sender_id),
        )
      else:
        await message.answer(
            "❌ Кечиресиз, бул форматтагы билдирүүнү азырынча кабыл ала"
            " албайбыз."
        )
        return

      if sent_message:
        await message.answer(
            "✅ Катыңыз анонимдүү түрдө ийгиликтүү жөнөтүлдү! 🥷✨"
        )

    except Exception:
      await message.answer(
          "❌ Тилекке каршы, билдирүү жетпей калды (алуучу ботту блок кылып"
          " койгон болушу мүмкүн)."
      )

  await state.clear()


# --- ЖОӨП БЕРҮҮГӨ КӨЧҮҮ ---
@dp.callback_query(F.data.startswith("reply_to_"))
async def callback_reply(callback: types.CallbackQuery, state: FSMContext):
  original_sender_id = callback.data.split("_")[2]
  await state.update_data(target_id=original_sender_id)

  await callback.message.answer(
      "↩️ **Жооп жазуу режими!**\n\nБул адамга кайрадан анонимдүү түрдө жооп"
      " жазыңыз. Ал сенин ким экениңди билбейт:\n\n✍️ Каалаган билдирүүнү"
      " жибериңиз:",
      parse_mode="Markdown",
  )
  await state.set_state(AnonymousStates.waiting_for_message)
  await callback.answer()


async def main():
  bot_info = await bot.get_me()
  print("--------------------------------------")
  print(f"✅ Бот ийгиликтүү иштеп баштады!")
  print(f"🤖 Bot Username: @{bot_info.username}")
  print(f"🔗 Channel link: {CHANNEL_LINK}")
  print("--------------------------------------")

  await bot.delete_webhook(drop_pending_updates=True)
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
