import io

from aiogram import Bot


async def download_photo(
    bot: Bot,
    file_id: str,
) -> io.BytesIO:
    file = await bot.get_file(file_id)
    buffer = io.BytesIO()
    await bot.download_file(file.file_path, destination=buffer)
    buffer.seek(0)
    return buffer
