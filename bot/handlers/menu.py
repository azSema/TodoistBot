from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.handlers.base import get_client, get_client_for_callback

router = Router()


class AddTaskStates(StatesGroup):
    waiting_for_task = State()


def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Active Tasks", callback_data="menu:pending")],
        [InlineKeyboardButton(text="✅ Completed Today", callback_data="menu:today")],
        [InlineKeyboardButton(text="📅 Completed This Week", callback_data="menu:week")],
        [InlineKeyboardButton(text="📆 Completed This Month", callback_data="menu:month")],
        [InlineKeyboardButton(text="📁 By Project", callback_data="menu:projects")]
    ])


def projects_keyboard(projects: dict, action: str = "pending"):
    buttons = []
    for project_id, name in sorted(projects.items(), key=lambda x: x[1]):
        buttons.append([InlineKeyboardButton(
            text=f"📁 {name}",
            callback_data=f"project:{action}:{name[:30]}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def project_actions_keyboard(project_name: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Active Tasks", callback_data=f"project:pending:{project_name}")],
        [InlineKeyboardButton(text="✅ Today", callback_data=f"project:today:{project_name}")],
        [InlineKeyboardButton(text="📅 Week", callback_data=f"project:week:{project_name}")],
        [InlineKeyboardButton(text="📆 Month", callback_data=f"project:month:{project_name}")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="menu:projects")]
    ])


def back_to_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="menu:main")]
    ])


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    client = await get_client(message)
    if not client:
        return
    
    await message.answer(
        "📊 **Todoist Dashboard**\n\nChoose an option:",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📊 **Todoist Dashboard**\n\nChoose an option:",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "menu:projects")
async def cb_projects_menu(callback: CallbackQuery):
    client = await get_client_for_callback(callback)
    if not client:
        return
    
    projects = await client.get_projects()
    if not projects:
        await callback.answer("No projects found")
        return
    
    await callback.message.edit_text(
        "📁 **Select a Project:**",
        reply_markup=projects_keyboard(projects),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("project:select:"))
async def cb_project_select(callback: CallbackQuery):
    project_name = callback.data.split(":", 2)[2]
    
    await callback.message.edit_text(
        f"📁 **{project_name}**\n\nWhat do you want to see?",
        reply_markup=project_actions_keyboard(project_name),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "menu:pending")
async def cb_pending_all(callback: CallbackQuery):
    client = await get_client_for_callback(callback)
    if not client:
        return
    
    await callback.answer("Loading...")
    tasks = await client.get_active_tasks()
    report = format_pending(tasks)
    
    await callback.message.edit_text(
        report,
        reply_markup=back_to_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "menu:today")
async def cb_today_all(callback: CallbackQuery):
    client = await get_client_for_callback(callback)
    if not client:
        return
    
    await callback.answer("Loading...")
    tasks = await client.get_today_completed()
    report = format_completed(tasks, "today")
    
    await callback.message.edit_text(
        report,
        reply_markup=back_to_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "menu:week")
async def cb_week_all(callback: CallbackQuery):
    client = await get_client_for_callback(callback)
    if not client:
        return
    
    await callback.answer("Loading...")
    tasks = await client.get_week_completed()
    report = format_completed(tasks, "this week")
    
    await callback.message.edit_text(
        report,
        reply_markup=back_to_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "menu:month")
async def cb_month_all(callback: CallbackQuery):
    client = await get_client_for_callback(callback)
    if not client:
        return
    
    await callback.answer("Loading...")
    tasks = await client.get_month_completed()
    report = format_completed(tasks, "this month")
    
    await callback.message.edit_text(
        report,
        reply_markup=back_to_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("project:"))
async def cb_project_action(callback: CallbackQuery):
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await callback.answer("Invalid action")
        return
    
    action = parts[1]
    project_name = parts[2]
    
    client = await get_client_for_callback(callback)
    if not client:
        return
    
    await callback.answer("Loading...")
    
    if action == "pending":
        tasks = await client.get_active_tasks()
        tasks = [t for t in tasks if t.project_name.lower() == project_name.lower()]
        report = format_pending(tasks, project_name)
    elif action == "today":
        tasks = await client.get_today_completed()
        tasks = [t for t in tasks if t.project_name.lower() == project_name.lower()]
        report = format_completed(tasks, "today", project_name)
    elif action == "week":
        tasks = await client.get_week_completed()
        tasks = [t for t in tasks if t.project_name.lower() == project_name.lower()]
        report = format_completed(tasks, "this week", project_name)
    elif action == "month":
        tasks = await client.get_month_completed()
        tasks = [t for t in tasks if t.project_name.lower() == project_name.lower()]
        report = format_completed(tasks, "this month", project_name)
    else:
        await callback.answer("Unknown action")
        return
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back to Project", callback_data=f"project:select:{project_name}")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu:main")]
    ])
    
    await callback.message.edit_text(
        report,
        reply_markup=back_kb,
        parse_mode="Markdown"
    )


def format_pending(tasks: list, project_name: str = None) -> str:
    title = f"📋 **Active Tasks**"
    if project_name:
        title += f" in {project_name}"
    
    if not tasks:
        return f"{title}\n\nNo active tasks. Nice! 🎉"
    
    lines = [f"{title}\n\nTotal: {len(tasks)}\n"]
    
    from collections import defaultdict
    by_project = defaultdict(list)
    for task in tasks:
        by_project[task.project_name].append(task)
    
    for project, project_tasks in sorted(by_project.items()):
        lines.append(f"\n📁 **{project}** ({len(project_tasks)})")
        for task in project_tasks:
            due = f" ⏰ {task.due_date}" if task.due_date else ""
            lines.append(f"  • {task.content}{due}")
    
    return "\n".join(lines)


def format_completed(tasks: list, period: str, project_name: str = None) -> str:
    title = f"✅ **Completed {period}**"
    if project_name:
        title += f" in {project_name}"
    
    if not tasks:
        return f"{title}\n\nNo completed tasks."
    
    lines = [f"{title}\n\nTotal: {len(tasks)}\n"]
    
    from collections import defaultdict
    by_project = defaultdict(list)
    for task in tasks:
        by_project[task.project_name].append(task)
    
    for project, project_tasks in sorted(by_project.items()):
        lines.append(f"\n📁 **{project}** ({len(project_tasks)})")
        for task in project_tasks:
            lines.append(f"  • {task.content}")
    
    return "\n".join(lines)


@router.callback_query(F.data == "menu:add_task")
async def cb_add_task(callback: CallbackQuery, state: FSMContext):
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="menu:main")]
    ])
    
    await callback.message.edit_text(
        "➕ **Add New Task**\n\n"
        "Send me the task text:",
        reply_markup=cancel_kb,
        parse_mode="Markdown"
    )
    await state.set_state(AddTaskStates.waiting_for_task)
    await callback.answer()


@router.message(AddTaskStates.waiting_for_task)
async def process_new_task(message: Message, state: FSMContext):
    from bot.handlers.base import get_client
    
    client = await get_client(message)
    if not client:
        await state.clear()
        return
    
    task_text = message.text.strip()
    success = await client.add_task(task_text)
    
    menu_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Another", callback_data="menu:add_task")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu:main")]
    ])
    
    if success:
        await message.answer(
            f"✅ Task added:\n\n• {task_text}",
            reply_markup=menu_kb
        )
    else:
        await message.answer(
            "❌ Failed to add task. Try again.",
            reply_markup=menu_kb
        )
    
    await state.clear()
