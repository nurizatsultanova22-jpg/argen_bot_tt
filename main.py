import requests
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# Сиздин токениңиз
TOKEN = "8620902917:AAHPuthkzK9MT7fGRWe2npjm4mY8ZwRXLWs"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Apple Music базасынан синхрондуу тез издөө
def search_apple_music_sync(query: str, limit: int = 4):
    url = f"https://itunes.apple.com/search?term={query}&entity=song&limit={limit}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            tracks = []
            for track in results:
                tracks.append({
                    "title": track.get("trackName"),
                    "artist": track.get("artistName"),
                    "album": track.get("collectionName"),
                    "cover": track.get("artworkUrl100", "").replace("100x100bb", "600x600bb"),
                    "link": track.get("trackViewUrl")
                })
            return tracks
    except Exception as e:
        print(f"Ката: {e}")
    return []

# /трек же /найти командалары
@dp.message(Command("трек", "найти"))
async def find_tracks_command(message: Message):
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "⚠️ Пожалуйста, укажите название трека после команды.\n"
            "Пример: `/трек камин` или `/найти камин`",
            parse_mode="Markdown"
        )
        return

    query = args[1]
    msg = await message.answer("⚡ Ищу треки...")

    tracks = search_apple_music_sync(query, limit=4)

    if not tracks:
        await msg.edit_text("❌ К сожалению, ничего не найдено.")
        return

    await msg.delete()

    for i, track in enumerate(tracks, 1):
        caption = (
            f"🎵 **Вариант {i}**\n"
            f"🎧 **Трек:** {track['title']}\n"
            f"🎤 **Исполнитель:** {track['artist']}\n"
            f"💿 **Альбом:** {track['album']}\n\n"
            f"🔗 [Слушать в Apple Music]({track['link']})"
        )

        if track["cover"]:
            await message.answer_photo(
                photo=track["cover"],
                caption=caption,
                parse_mode="Markdown"
            )
        else:
            await message.answer(caption, parse_mode="Markdown")

if __name__ == "__main__":
    dp.run_polling(bot)
