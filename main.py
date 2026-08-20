import random
from aiogram import Bot, Dispatcher, types

# Токениң туура кошулду
TOKEN = "8943857517:AAHKx8raz2WrxYeHI2hjE1f5TpnygJq2vZE"

BOT_LABEL = "🤖 ᴀʀsᴇɴ ʙᴏᴛ | "
emojis = ["🚀", "✨", "🔥", "⚡", "👨‍💻", "💼", "🤖", "😎", "💬", "🎯", "📌"]

bot = Bot(token=TOKEN)
dp = Dispatcher()


def get_smart_reply(incoming_text):
  text = incoming_text.lower()
  emo = random.choice(emojis)

  if any(word in text for word in ["салам", "кутман", "привет", "хай", "алло"]):
    reply = f"Салам! {emo} Аргендин жеке жардамчысы Арсенмин. Учурда Арген бош эмес, сурооңуз болсо калтырыңыз, мен жазып алам!"
  elif any(word in text for word in ["жумуш", "заказ", "проект", "иш", "бот"]):
    reply = f"Техникалык маселе же сунуш боюнча билдирүүңүздү кабыл алдым. {emo} Арген бошоор менен сөзсүз карап чыгат."
  else:
    reply = f"Билдирүүңүз үчүн рахмат! {emo} Сурооңузду ('{incoming_text}') кабыл алдым, Арген келгенде өзү жооп берет."

  return f"{BOT_LABEL}\n{reply}"


@dp.message()
async def handle_message(message: types.Message):
  reply_text = get_smart_reply(message.text)
  await message.reply(reply_text)


async def main():
  print("Арсен бот иштеп баштады... 🚀")
  await dp.start_polling(bot)


if __name__ == "__main__":
  import asyncio

  asyncio.run(main())
