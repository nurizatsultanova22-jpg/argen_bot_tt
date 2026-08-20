import os
from telethon import TelegramClient, events

# my.telegram.org сайтынан алган маалыматтарың
api_id = 36507092
api_hash = "эң башында алган api_hash маалыматыңды жаз" # <-- Бул жерге жазасың

# Сессия файлы GitHub'дан кошо келгендиктен, ал кайра номер сурабайт
client = TelegramClient('argen_session', api_id, api_hash)

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    sender = await event.get_sender()
    # Өзүңө өзүң жазбаш үчүн жана башкалардан келген катка жооп берүү үчүн
    if not sender.is_self:
        await event.reply("Салам! Арген учурда бош эмес, бошоор менен өзгөчө жооп берет.")

async def main():
    print("UserBot Render аркылуу ишке кирди... 🚀")
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
