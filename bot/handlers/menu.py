from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from collections import defaultdict

from bot.handlers.base import get_client, get_client_for_callback
from bot.ai_reports import generate_report

router = Router()

tasks_cache = {}


def main_menu_keyboard(projects: dict):
    buttons = []
    for project_id, name in sorted(projects.items(), key=lambda x: x[1]):
        buttons.append([InlineKeyboardButton(
            text=f"📁 {name}",
            callback_data=f"project:{project_id}:{name[:20]}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def project_keyboard(project_id: str, project_name: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Отчёт за сегодня", callback_data=f"report:daily:{project_id}:{project_name}")],
        [InlineKeyboardButton(text="📆 Отчёт за месяц", callback_data=f"report:monthly:{project_id}:{project_name}")],
        [InlineKeyboardButton(text="⬅️ Назад к проектам", callback_data="menu:main")]
    ])


def back_keyboard(project_id: str = "", project_name: str = ""):
    buttons = []
    if project_id:
        buttons.append([InlineKeyboardButton(text="🔄 Сгенерировать заново", callback_data=f"report:daily:{project_id}:{project_name}")])
        buttons.append([InlineKeyboardButton(text="⬅️ К проекту", callback_data=f"project:{project_id}:{project_name}")])
    buttons.append([InlineKeyboardButton(text="🏠 К проектам", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("start"))
async def cmd_start(message: Message):
    client = await get_client(message)
    if not client:
        return
    
    projects = await client.get_projects()
    if not projects:
        await message.answer("Нет проектов в Todoist. Создай проект и возвращайся!")
        return
    
    await message.answer(
        "📊 Выбери проект для отчёта:",
        reply_markup=main_menu_keyboard(projects)
    )


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery):
    client = await get_client_for_callback(callback)
    if not client:
        return
    
    projects = await client.get_projects()
    if not projects:
        await callback.answer("Нет проектов")
        return
    
    await callback.message.edit_text(
        "📊 Выбери проект для отчёта:",
        reply_markup=main_menu_keyboard(projects)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("project:"))
async def cb_select_project(callback: CallbackQuery):
    parts = callback.data.split(":", 2)
    project_id = parts[1]
    project_name = parts[2] if len(parts) > 2 else "Проект"
    
    await callback.message.edit_text(
        f"📁 {project_name}\n\nКакой отчёт сформировать?",
        reply_markup=project_keyboard(project_id, project_name)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("report:"))
async def cb_generate_report(callback: CallbackQuery):
    parts = callback.data.split(":", 3)
    report_type = parts[1]
    project_id = parts[2]
    project_name = parts[3] if len(parts) > 3 else ""
    
    client = await get_client_for_callback(callback)
    if not client:
        return
    
    await callback.answer("⏳ Загружаю задачи...")
    await callback.message.edit_text("⏳ Загружаю задачи из Todoist...")
    
    if report_type == "daily":
        tasks = await client.get_today_completed()
    else:
        tasks = await client.get_month_completed()
    
    tasks = [t for t in tasks if t.project_name.lower() == project_name.lower()]
    
    if not tasks:
        period = "сегодня" if report_type == "daily" else "этот месяц"
        await callback.message.edit_text(
            f"📁 {project_name}\n\nНет выполненных задач за {period}.",
            reply_markup=back_keyboard(project_id, project_name)
        )
        return
    
    await callback.message.edit_text("🤖 Генерирую отчёт...")
    
    tasks_text = "\n".join([f"- {t.content}" for t in tasks])
    ai_report = await generate_report(tasks_text, report_type)
    
    if not ai_report:
        await callback.message.edit_text(
            f"❌ Не удалось сгенерировать отчёт.\n\n"
            f"Проверь GEMINI_API_KEY в Railway.\n\n"
            f"Задачи ({len(tasks)}):\n" + tasks_text,
            reply_markup=back_keyboard(project_id, project_name)
        )
        return
    
    report_title = "📅 Дневной отчёт" if report_type == "daily" else "📆 Месячный отчёт"
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Заново", callback_data=callback.data)],
        [InlineKeyboardButton(text="⬅️ К проекту", callback_data=f"project:{project_id}:{project_name}")],
        [InlineKeyboardButton(text="🏠 К проектам", callback_data="menu:main")]
    ])
    
    await callback.message.edit_text(
        f"{report_title} | {project_name}\n\n{ai_report}",
        reply_markup=back_kb
    )
