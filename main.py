import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
import yt_dlp

TOKEN = "8981337963:AAG0tCPAwXo1ldR20VMLODwKPKnsBqgdi4Q"

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

def download_audio(query: str):
    """YouTube/SoundCloud'тан тректи издеп, аудио файл катары түшүрүү"""
    output_template = 'downloaded_audio.mp3'
    if os.path.exists(output_template):
        try:
            os.remove(output_template)
        except:
            pass

    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1', # Биринчи чыккан музыканы алат (DRM каталарын четтетүү үчүн)
        'outtmpl': 'downloaded_audio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'noplaylist': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=True)
            # Файлдын атын табуу
            filename = 'downloaded_audio.mp3'
            if os.path.exists(filename):
                return filename, info.get('title', 'Музыка')
        except Exception as e:
            logging.error(f"Жүктөө катасы: {e}")
            return None, None
    return None, None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Салам! Мен музыка таап берүүчү ботмун 🎵\n\n"
        "Мага каалаган ырдын атын жазып жибериңиз, мен аны издеп, сизге **түздөн-түз аудио файл (mp3)** кылып жөнөтөм!"
    )

@dp.message(F.text)
async def send_audio_track(message: types.Message):
    query = message.text.strip()
    if query.startswith("/"):
        return

    wait_msg = await message.answer("🔍 Музыка изделүүдө жана даярдалууда, күтө туруңуз...")

    loop = asyncio.get_running_loop()
    filename, title = await loop.run_in_executor(None, download_audio, query)

    await wait_msg.delete()

    if not filename or not os.path.exists(filename):
        await message.answer("❌ Тилекке каршы, бул музыка табылган жок же аны жүктөп болбоду.")
        return

    try:
        audio_file = types.FSInputFile(filename)
        await message.answer_audio(audio=audio_file, caption=f"🎵 {title}")
    except Exception as e:
        await message.answer(f"❌ Жөнөтүүдө ката кетти: {e}")
    finally:
        # Файлды өчүрүп тазалоо
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

async def main():
    print("Музыка жүктөөчү бот ишке кирди!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
