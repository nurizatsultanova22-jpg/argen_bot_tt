import random
from telethon import TelegramClient, events

# Сенин api_id жана api_hash маалыматтарың
api_id = 36507092
api_hash = "10e840d07af74d2882b11de01394d308"

# Боттун отметкасы жана ар кандай заманбап эмодзилер тизмеси
BOT_LABEL = "🤖 ᴀʀsᴇɴ ʙᴏᴛ | "
emojis = ["🚀", "✨", "🔥", "⚡", "👨‍💻", "💼", "🤖", "😎", "💬", "🎯", "📌"]

# Сессия түзөбүз
client = TelegramClient("argen_session", api_id, api_hash)


# Суроолорго жараша акылдуу жана эмодзи кошулган жоопторду тандоо
def get_smart_reply(incoming_text):
  text = incoming_text.lower()
  emo = random.choice(emojis)

  # 1. Саламдашуу
  if any(word in text for word in ["салам", "кутман", "привет", "хай", "алло"]):
    reply = f"Салам! {emo} Аргендин жеке жардамчысы Арсенмин. Учурда Арген бош эмес, сурооңуз болсо калтырыңыз, мен жазып алам!"

  # 2. Жумуш же долбоор боюнча
  elif any(word in text for word in ["жумуш", "заказ", "проект", "иш", "бот"]):
    reply = f"Техникалык маселе же сунуш боюнча билдирүүңүздү кабыл алдым. {emo} Арген бошоор менен сөзсүз карап чыгат."

  # 3. Башка бардык учурлар үчүн
  else:
    reply = f"Билдирүүңүз үчүн рахмат! {emo} Сурооңузду ('{incoming_text}') кабыл алдым, Арген келгенде өзү жооп берет."

  return f"{BOT_LABEL}\n{reply}"


# Личкага (жеке билдирүүлөргө) келген каттар
@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def private_reply(event):
  await event.reply(get_smart_reply(event.raw_text))


# Группага келген каттар (эгер сени белгилесе / mention кылса)
@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_group))
async def group_reply(event):
  if event.mentioned:
    emo = random.choice(emojis)
    await event.reply(
        f"{BOT_LABEL}\nАрген учурда жумушта. {emo} Сурооңузду («{event.raw_text}») каттап койдум, кийинчерээк байланышат!"
    )


print("Арсен бот иштеп баштады... 🚀")
client.start()
client.run_until_disconnected()
