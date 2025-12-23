from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database import get_user_token, save_user_token
from bot.todoist_client import TodoistClient

router = Router()

TODOIST_TOKEN_URL = "https://app.todoist.com/app/settings/integrations/developer"


class SetupStates(StatesGroup):
    waiting_for_token = State()


def get_token_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Get API Token", url=TODOIST_TOKEN_URL)]
    ])


def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Active Tasks", callback_data="menu:pending")],
        [InlineKeyboardButton(text="✅ Completed Today", callback_data="menu:today")],
        [InlineKeyboardButton(text="📅 This Week", callback_data="menu:week")],
        [InlineKeyboardButton(text="📆 This Month", callback_data="menu:month")],
        [InlineKeyboardButton(text="📁 By Project", callback_data="menu:projects")],
        [InlineKeyboardButton(text="➕ Add Task", callback_data="menu:add_task")]
    ])


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    token = await get_user_token(message.from_user.id)
    
    if token:
        await message.answer(
            "📊 **Todoist Dashboard**\n\n"
            "Choose an option below or use commands:\n"
            "`/today` `/week` `/month` `/pending` `/add`",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "👋 **Welcome to Todoist Report Bot!**\n\n"
            "To get started, I need your Todoist API token.\n\n"
            "1️⃣ Click the button below\n"
            "2️⃣ Scroll down to 'API token'\n"
            "3️⃣ Copy and send it here",
            reply_markup=get_token_keyboard(),
            parse_mode="Markdown"
        )
        await state.set_state(SetupStates.waiting_for_token)


@router.message(Command("setkey"))
async def cmd_setkey(message: Message, state: FSMContext):
    await message.answer(
        "🔑 Click the button to get your API token.\n"
        "Then send it to me.",
        reply_markup=get_token_keyboard()
    )
    await state.set_state(SetupStates.waiting_for_token)


@router.message(SetupStates.waiting_for_token)
async def process_token(message: Message, state: FSMContext):
    token = message.text.strip()
    
    if len(token) < 20:
        await message.answer("❌ This doesn't look like a valid token. Please try again.")
        return
    
    await message.answer("🔄 Verifying your token...")
    
    client = TodoistClient(token)
    if await client.verify_token():
        await save_user_token(message.from_user.id, token)
        await state.clear()
        await message.answer(
            "✅ **Success!** Your Todoist account is connected.\n\n"
            "Choose an option:",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "❌ Invalid token. Please check and try again.\n"
            "Make sure you copied the full token.",
            reply_markup=get_token_keyboard()
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 **Todoist Report Bot**\n\n"
        "**Interactive Menu:**\n"
        "/start - Open dashboard with buttons\n\n"
        "**Text Commands:**\n"
        "/today - Completed today\n"
        "/today Work - Today in 'Work' project\n"
        "/week - Completed this week\n"
        "/month - Completed this month\n"
        "/pending - Active tasks\n"
        "/projects - List all projects\n"
        "/add <task> - Add new task\n\n"
        "**Settings:**\n"
        "/setkey - Change API key\n"
        "/help - This message",
        parse_mode="Markdown"
    )
