import aiohttp
import io
from aiogram.types import Message
from aiogram.types import ContentType

async def download_photo_from_telegram(bot, file_id: str) -> io.BytesIO:
    file = await bot.get_file(file_id)
    file_path = file.file_path
    telegram_file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(telegram_file_url) as resp:
            if resp.status == 200:
                file_content = await resp.read()
                return io.BytesIO(file_content)
            else:
                raise Exception(f"Couldn't dowload photo from Telegram: {resp.status}")

async def validate_photo(message: Message) -> tuple[bool, str]:
    if message.content_type != ContentType.PHOTO:
        return False, "Please send a photo in JPG or PNG format."

    if not message.photo:
        return False, "No photo found in the message."

    photo = message.photo[-1]

    if photo.file_size > 10 * 1024 * 1024:
        return False, f"Photo size exceeds the limit of 10 MB."

    return True, photo.file_id