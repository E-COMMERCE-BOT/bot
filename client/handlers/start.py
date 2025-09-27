import logging
import aiohttp
from aiogram import Router
from aiogram.types import Message as AiogramMessage
from aiogram.filters import CommandStart
from aiohttp import ClientConnectorError, ServerTimeoutError
from aiogram.fsm.context import FSMContext

from data.config import config_settings
from data.url import url_users
from client.keyboards.inline import main_keyboard

logger = logging.getLogger(__name__)

start_router = Router()

@start_router.message(CommandStart())
async def cmd_start(message: AiogramMessage, state: FSMContext):
    await state.clear()

    user_data = {
        "tg_id": message.from_user.id,
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            try:
                async with session.post(
                        url_users,
                        json=user_data,
                        headers={"X-Bot-Api-Key": config_settings.BOT_API_KEY.get_secret_value()}
                ) as resp:
                    response_data = await resp.json()

                    if resp.status in (200, 201):
                        greeting_name = response_data.get('first_name', message.from_user.first_name)
                        if resp.status == 201:
                            greeting_text = (
                                "<b>Welcome to E-Commerce Bot!</b>\n\n"
                                "Here you can browse different clothes and place your orders."
                            )

                            await message.answer(
                                greeting_text,
                                parse_mode="HTML",
                                reply_markup=main_keyboard()
                            )

                        elif resp.status == 200:
                            greeting_text = "We are happy to see you again."

                            await message.answer(
                                f"Welcome back to E-Commerce Bot, <b>{greeting_name}</b>!\n\n"
                                f"{greeting_text}",
                                parse_mode="HTML",
                                reply_markup=main_keyboard()
                            )

                    else:
                        error_msg = response_data.get('detail', 'The service is temporarily unavailable.')
                        logger.error(f"API error {resp.status}: {error_msg}")
                        await message.answer(
                            f"{error_msg}\n\n"
                            "Please try again later."
                        )

            except ServerTimeoutError:
                logger.error("Server timeout error")
                await message.answer(
                    f"⏳ <b>{message.from_user.first_name}</b>, the server is not responding.\n"
                    "Please try again later."
                )

            except ClientConnectorError as e:
                logger.error(f"Connection error: {str(e)}")
                await message.answer(
                    f"<b>Technical issues</b>\n\n"
                    f"Hello, <b>{message.from_user.first_name}</b>!\n"
                    "Could not connect to the server.\n\n"
                    "Our team is already working on this issue.\n"
                    "Please try again in 15-20 minutes."
                )

            except Exception as e:
                logger.error(f"Unexpected request error: {str(e)}")
                await message.answer(
                    f"<b>Unexpected error</b>\n\n"
                    f"Hello, <b>{message.from_user.first_name}</b>!\n"
                    "An unexpected error occurred.\n\n"
                    "Our team is already aware and working on a fix."
                )

    except Exception as e:
        logger.error(f"Critical error: {str(e)}", exc_info=True)
        await message.answer(
            f"<b>{message.from_user.first_name}</b>, welcome!\n"
            "The service is temporarily limited, but basic functions are available.",
            reply_markup=main_keyboard()
        )
