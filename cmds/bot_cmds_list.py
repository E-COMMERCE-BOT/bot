"""Public bot commands exposed to Telegram clients.

The list is used in `bot/run.py` to set commands via `set_my_commands`.
Keep descriptions short and localized as needed.
"""

from aiogram.types import BotCommand

# Commands visible in the client's command menu (private chats scope).
bot_cmds_list = [
    BotCommand(command="start", description="Start bot"),
    BotCommand(command="admin", description="Admin panel"),
]
