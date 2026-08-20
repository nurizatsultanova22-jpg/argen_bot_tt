import asyncio
from aiogram import Bot, Dispatcher, types

TOKEN = "8512573395:AAEn-4ULOTRv5gbrZxp9Dgp_yaHHxLVsQYo"
MY_ID = 36507092  # Өзүңдүн ID'ң

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message()
async def echo_handler(message: types.Message):
  try:
    # 1. Келген катты сага forward кылат
    await bot.forward_message(
        chat_id=MY_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )

    # 2. Келген текстти текшерип, ар кандай жооп кайтарат
    text = message.text.lower() if message.text else ""

    if any(
        word in text for word in ["салам", "кутман", "привет", "хай", "алло"]
    ):
      reply = "Салам! Арген учурда бош эмес, бирок кабарыңызды окуп чыгат."
    elif any(word in text for word in ["жумуш", "заказ", "проект", "иш", "бот"]):
      reply = "Бул сунуш же заказ боюнча маалымат кабыл алынды. Арген бошогондо байланышат!"
    else:
      reply = "Билдирүүңүз Аргенге түздөн-түз жөнөтүлдү, рахмат!"

    await message.answer(reply)

  except Exception as e:
    print(f"Ката чыкты: {e}")


async def main():
  print("Бот иштеп жатат...")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
