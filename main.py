import asyncio
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# Сиз берген токен туташтырылды
TOKEN = "8620902917:AAHPuthkzK9MT7fGRWe2npjm4mY8ZwRXLWs"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Apple Music'тен 4 вариантты жогорку ылдамдыкта издөө
async def search_apple_music_multiple(query: str, limit: int = 4):
    url = f"https://itunes.apple.com/search?term={query}&entity=song&limit={limit}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                results = data.get("results", [])
                tracks = []
                for track in results:
                    tracks.append({
                        "title": track.get("trackName"),
                        "artist": track.get("artistName"),
                        "album": track.get("collectionName"),
                        "cover": track.get("artworkUrl100").replace("100x100bb", "600x600bb"), # Эң жогорку сапаттагы сүрөт
                        "link": track.get("trackViewUrl")
                    })
                return tracks
    return []

@dp.message(Command("track", "find"))
async def find_tracks_command(message: Message):
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer("⚠️ Сураныч, командадан кийин ырдын атын жазыңыз.\nМисалы: `/track Сени күтөм`", parse_mode="Markdown")
        return

    query = args[1]
    msg = await message.answer("⚡ Тез изделүүдө...")

    tracks = await search_apple_music_multiple(query, limit=4)

    if not tracks:
        await message.edit_text("❌ Тилекке каршы, эч нерсе табылган жок.")
        return

    await msg.delete()

    # Табылган 4 вариантты сүрөтү жана сапаты менен катар жөнөтөбүз
    for i, track in enumerate(tracks, 1):
        caption = (
            f"🎵 **Вариант {i}**\n"
            f"🎧 **Ыр:** {track['title']}\n"
            f"🎤 **Аткаруучу:** {track['artist']}\n"
            f"💿 **Альбом:** {track['album']}\n\n"
            f"🔗 [Apple Music'тен угуу]({track['link']})"
        )

        if track["cover"]:
            await message.answer_photo(
                photo=track["cover"],
                caption=caption,
                parse_mode="Markdown"
            )
        else:
            await message.answer(caption, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
