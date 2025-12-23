from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database import get_user_token, save_user_token
from bot.todoist_client import TodoistClient

router = Router()

TODOIST_TOKEN_URL = "todoist://settings/integrations/developer"
TODOIST_TOKEN_URL_WEB = "https://app.todoist.com/app/settings/integrations/developer"


class SetupStates(StatesGroup):
    waiting_for_token = State()


def get_token_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Open Todoist App", url=TODOIST_TOKEN_URL)],
        [InlineKeyboardButton(text="Open in Browser", url=TODOIST_TOKEN_URL_WEB)]
    ])


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    token = await get_user_token(message.from_user.id)
    
    if token:
        await message.answer(
            "Welcome back! Your Todoist is already connected.\n\n"
            "Commands:\n"
            "/today - tasks completed today\n"
            "/week - tasks completed this week\n"
            "/month - tasks completed this month\n"
            "/pending - active tasks\n"
            "/projects - list all projects\n"
            "/add <task> - add new task\n"
            "/setkey - change Todoist API key\n"
            "/help - show all commands"
        )
    else:
        await message.answer(
            "Welcome to Todoist Report Bot!\n\n"
            "To get started, I need your Todoist API token.\n\n"
            "1. Click the button below\n"
            "2. Scroll down to 'API token'\n"
            "3. Copy and send it to me",
            reply_markup=get_token_keyboard()
        )
        await state.set_state(SetupStates.waiting_for_token)


@router.message(Command("setkey"))
async def cmd_setkey(message: Message, state: FSMContext):
    await message.answer(
        "Click the button to get your new API token.\n"
        "Then send it to me.",
        reply_markup=get_token_keyboard()
    )
    await state.set_state(SetupStates.waiting_for_token)


@router.message(SetupStates.waiting_for_token)
async def process_token(message: Message, state: FSMContext):
    token = message.text.strip()
    
    if len(token) < 20:
        await message.answer("This doesn't look like a valid token. Please try again.")
        return
    
    await message.answer("Verifying your token...")
    
    client = TodoistClient(token)
    if await client.verify_token():
        await save_user_token(message.from_user.id, token)
        await state.clear()
        await message.answer(
            "Success! Your Todoist account is now connected.\n\n"
            "Try /today to see what you've completed today!"
        )
    else:
        await message.answer(
            "Invalid token. Please check and try again.\n"
            "Make sure you copied the full token from todoist.com/prefs/integrations"
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Todoist Report Bot Commands:\n\n"
        "Reports:\n"
        "/today - tasks completed today\n"
        "/today Work - today in project 'Work'\n"
        "/week - tasks completed this week\n"
        "/week Personal - week in project 'Personal'\n"
        "/month - tasks completed this month\n"
        "/pending - show active tasks\n"
        "/projects - list all projects\n\n"
        "Task Management:\n"
        "/add <task> - add new task to Inbox\n\n"
        "Settings:\n"
        "/setkey - change your Todoist API key\n"
        "/help - show this message"
    )
