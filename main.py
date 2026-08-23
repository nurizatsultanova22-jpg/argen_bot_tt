import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
import aiohttp
import os

# Telegram ботуңуздун токени
TOKEN = "СИЗДИН_БОТ_ТОКЕНИНИЗ"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Издөө жана аудио файлды жүктөө функциясы
async def search_and_download_track(query: str):
    # Ачык музыкалык база аркылуу ырды издейбиз
    search_url = f"https://api.deezer.com/search?q={query}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as response:
            if response.status != 200:
                return None, "Базага туташууда ката кетти."
            
            data = await response.json()
            tracks = data.get("data", [])
            
            if not tracks:
                return None, "Ыр табылган жок. Башка атын жазып көрүңүз."
            
            # Биринчи табылган тректи алабыз (анын preview шилтемеси же толук трек маалыматы)
            track = tracks[0]
            track_title = f"{track['artist']['name']} - {track['title']}"
            preview_url = track.get("preview")  # 30 секунддук же толук аудио агым шилтемеси
            
            if not preview_url:
                return None, "Бул ырдын аудио файлы жеткиликсиз экен."
            
            # Файлды убактылуу сактап калабыз
            file_path = "temp_audio.mp3"
            async with session.get(preview_url) as audio_resp:
                if audio_resp.status == 200:
                    with open(file_path, "wb") as f:
                        f.write(await audio_resp.read())
                    return file_path, track_title
                    
    return None, "Ырды жүктөөдө ката кетти."

# '/трек [аты]' буйругун кармоо
@dp.message(F.text.startswith("трек "))
async def send_track(message: types.Message):
    # 'трек ' деген сөздөн кийинки ырдын атын алабыз
    query = message.text[5:].strip()
    
    if not query:
        await message.answer("Сураныч, ырдын атын да кошо жазыңыз. Мисалы: `трек Камин`", parse_mode="Markdown")
        vreturn
        
    waiting_msg = await message.answer("🎵 Ыр изделүүдө жана даярдалууда...")
    
    file_path, title_or_error = await search_and_download_track(query)
    
    if file_path:
        # Таза аудио файлды Telegram'га жөнөтөбүз
        audio = FSInputFile(file_path)
        await message.answer_audio(audio=audio, caption=f"🎧 {title_or_error}")
        await waiting_msg.delete()
        
        # Колдонулуп бүткөн убактылуу файлды өчүрөбүз
        if os.path.exists(file_path):
            os.remove(file_path)
    else:
        await waiting_msg.edit_text(title_or_error)

async def main():
    print("Бот ишке кирди...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
