"""Utilities for validating and downloading photos from Telegram.

Used in product creation/edit flows to ensure proper image handling
before uploading to the backend.
"""

import aiohttp
import io
from aiogram.types import Message
from aiogram.types import ContentType


async def download_photo_from_telegram(bot, file_id: str) -> io.BytesIO:
    """Download a Telegram file by id and return its bytes as BytesIO."""
    file = await bot.get_file(file_id)
    file_path = file.file_path
    telegram_file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"

    async with aiohttp.ClientSession() as session:
        async with session.get(telegram_file_url) as resp:
            if resp.status == 200:
                file_content = await resp.read()
                return io.BytesIO(file_content)
            else:
                # Bubble up a clear error if Telegram returns a non-200 status.
                raise Exception(
                    f"Couldn't dowload photo from Telegram: {resp.status}"
                )


async def validate_photo(message: Message) -> tuple[bool, str]:
    """Validate that a message contains a photo and meets basic constraints.

    Returns a tuple of (is_valid, value). On success, `value` is the file_id.
    On failure, `value` contains a human-friendly error message.
    """
    if message.content_type != ContentType.PHOTO:
        return False, "Please send a photo in JPG or PNG format."

    if not message.photo:
        return False, "No photo found in the message."

    # Use the highest-resolution photo variant (last in the list).
    photo = message.photo[-1]

    # Enforce a 10 MB size limit.
    if photo.file_size > 10 * 1024 * 1024:
        return False, "Photo size exceeds the limit of 10 MB."

    return True, photo.file_id
