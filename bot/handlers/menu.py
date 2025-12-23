from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from bot.handlers.base import get_client, get_client_for_callback
from bot.ai_reports import generate_report, filter_work_tasks

router = Router()


def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Отчёт за сегодня", callback_data="report:daily")],
        [InlineKeyboardButton(text="📆 Отчёт за месяц", callback_data="report:monthly")]
    ])


def back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")]
    ])


@router.message(Command("start"))
async def cmd_start(message: Message):
    client = await get_client(message)
    if not client:
        return
    
    await message.answer(
        "📊 Отчёты по Todoist\n\nВыбери период:",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📊 Отчёты по Todoist\n\nВыбери период:",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("report:"))
async def cb_generate_report(callback: CallbackQuery):
    report_type = callback.data.split(":")[1]
    
    client = await get_client_for_callback(callback)
    if not client:
        return
    
    await callback.answer("⏳ Загружаю задачи...")
    await callback.message.edit_text("⏳ Загружаю задачи из Todoist...")
    
    if report_type == "daily":
        tasks = await client.get_today_completed()
        period_text = "сегодня"
    else:
        tasks = await client.get_month_completed()
        period_text = "этот месяц"
    
    tasks = filter_work_tasks(tasks)
    
    if not tasks:
        await callback.message.edit_text(
            f"Нет выполненных задач за {period_text}.",
            reply_markup=back_keyboard()
        )
        return
    
    await callback.message.edit_text(f"🤖 Генерирую отчёт по {len(tasks)} задачам...")
    
    tasks_text = "\n".join([f"- {t.content} (проект: {t.project_name})" for t in tasks])
    ai_report = await generate_report(tasks_text, report_type)
    
    if not ai_report:
        await callback.message.edit_text(
            f"❌ Не удалось сгенерировать отчёт.\n\n"
            f"Проверь GEMINI_API_KEY в Railway.\n\n"
            f"Задачи ({len(tasks)}):\n" + tasks_text[:2000],
            reply_markup=back_keyboard()
        )
        return
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Заново", callback_data=callback.data)],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")]
    ])
    
    await callback.message.edit_text(
        ai_report,
        reply_markup=back_kb,
        parse_mode="HTML"
    )
