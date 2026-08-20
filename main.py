import asyncio
from aiogram import Bot, Dispatcher, types

TOKEN = "8512573395:AAEn-4ULOTRv5gbrZxp9Dgp_yaHHxLVsQYo"
MY_ID = 36507092  # Өзүңдүн Telegram ID'ң (эгер башка болсо өзгөртөсүң)

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message()
async def echo_handler(message: types.Message):
  # Ким жазганын билип туруп, сага forward кылат
  await bot.forward_message(
      chat_id=MY_ID, from_chat_id=message.chat.id, message_id=message.message_id
  )
  # Жана жазган адамга автоматтык түрдө жооп кайтарат
  await message.answer(
      "Билдирүүңүз Аргенге жөнөтүлдү, ал бошоор менен сөзсүз жооп берет!"
  )


async def main():
  print("Бот иштеп баштады...")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
