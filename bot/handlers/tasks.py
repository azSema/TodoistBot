from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from bot.handlers.base import get_client

router = Router()


@router.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject):
    client = await get_client(message)
    if not client:
        return
    
    if not command.args:
        await message.answer("Usage: /add <task text>\n\nExample: /add Buy groceries")
        return
    
    task_text = command.args
    success = await client.add_task(task_text)
    
    if success:
        await message.answer(f"Added to Inbox: {task_text}")
    else:
        await message.answer("Failed to add task. Please try again.")
