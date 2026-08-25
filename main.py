import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
import yt_dlp

TOKEN = "8981337963:AAG0tCPAwXo1ldR20VMLODwKPKnsBqgdi4Q"

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

def search_soundcloud(query: str):
    """SoundCloud платформасынан трек издөө функциясы"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'scsearch5',  # SoundCloud'тан 5 трек табат
        'noplaylist': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                return info['entries']
            return [info]
        except Exception as e:
            logging.error(f"Издөө катасы: {e}")
            return []

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Салам! Мен **SoundCloud** музыка издөөчү ботмун 🎵\n\n"
        "Мага каалаган ырдын же аткаруучунун атын жазып жибериңиз, мен сизге SoundCloud'тан тректерди таап берем!"
    )

@dp.message(F.text)
async def search_track(message: types.Message):
    query = message.text.strip()
    
    if query.startswith("/"):
        return

    wait_msg = await message.answer("🔍 SoundCloud'тан изделүүдө, күтө туруңуз...")

    # Функцияны асинхрондуу түрдө аткаруу
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, search_soundcloud, query)

    await wait_msg.delete()

    if not results:
        await message.answer("❌ Тилекке каршы, эч нерсе табылган жок. Башка атын жазып көрүңүз.")
        return

    response = f"🎵 **'{query}' боюнча табылган тректер:**\n\n"
    
    for i, track in enumerate(results[:5], 1):
        title = track.get('title', 'Аталышы жок')
        url = track.get('webpage_url', '#')
        uploader = track.get('uploader', 'Белгисиз автор')
        
        response += f"{i}. **{title}** — *{uploader}*\n🔗 {url}\n\n"

    await message.answer(response, parse_mode="Markdown", disable_web_page_preview=True)

async def main():
    print("SoundCloud бот ишке кирди!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
