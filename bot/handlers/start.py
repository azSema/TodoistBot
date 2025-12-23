from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
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
        [InlineKeyboardButton(text="🔑 Получить API Token", url=TODOIST_TOKEN_URL)]
    ])


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    token = await get_user_token(message.from_user.id)
    
    if token:
        from bot.handlers.menu import main_menu_keyboard
        await message.answer(
            "📊 Отчёты по Todoist\n\nВыбери период:",
            reply_markup=main_menu_keyboard()
        )
    else:
        await message.answer(
            "👋 Привет! Это бот для отчётов по Todoist.\n\n"
            "Для начала нужен твой API токен:\n"
            "1. Нажми кнопку ниже\n"
            "2. Скопируй API token\n"
            "3. Отправь его сюда",
            reply_markup=get_token_keyboard()
        )
        await state.set_state(SetupStates.waiting_for_token)


@router.message(Command("setkey"))
async def cmd_setkey(message: Message, state: FSMContext):
    await message.answer(
        "🔑 Отправь новый API токен:",
        reply_markup=get_token_keyboard()
    )
    await state.set_state(SetupStates.waiting_for_token)


@router.message(SetupStates.waiting_for_token)
async def process_token(message: Message, state: FSMContext):
    token = message.text.strip()
    
    if len(token) < 20:
        await message.answer("❌ Это не похоже на токен. Попробуй ещё раз.")
        return
    
    await message.answer("🔄 Проверяю токен...")
    
    client = TodoistClient(token)
    if await client.verify_token():
        await save_user_token(message.from_user.id, token)
        await state.clear()
        
        from bot.handlers.menu import main_menu_keyboard
        await message.answer(
            "✅ Готово! Выбери период:",
            reply_markup=main_menu_keyboard()
        )
    else:
        await message.answer(
            "❌ Неверный токен. Проверь и попробуй снова.",
            reply_markup=get_token_keyboard()
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 Команды:\n\n"
        "/start - выбор проекта\n"
        "/setkey - сменить токен Todoist\n"
        "/help - эта справка"
    )
