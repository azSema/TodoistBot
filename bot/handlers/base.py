from aiogram import Router
from aiogram.types import Message, CallbackQuery
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


async def get_client_for_callback(callback: CallbackQuery) -> Optional[TodoistClient]:
    token = await get_user_token(callback.from_user.id)
    if not token:
        await callback.answer("Please use /start to connect your Todoist account", show_alert=True)
        return None
    return TodoistClient(token)
