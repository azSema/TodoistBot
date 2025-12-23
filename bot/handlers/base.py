from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from typing import Optional

from bot.database import get_user_token
from bot.todoist_client import TodoistClient

router = Router()


async def get_client(message: Message) -> Optional[TodoistClient]:
    token = await get_user_token(message.from_user.id)
    if not token:
        await message.answer(
            "You haven't connected your Todoist account yet.\n"
            "Use /start to set up your API token."
        )
        return None
    return TodoistClient(token)
