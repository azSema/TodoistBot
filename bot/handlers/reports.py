from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from datetime import datetime
from collections import defaultdict

from bot.handlers.base import get_client
from bot.todoist_client import TaskInfo

router = Router()


def format_tasks_report(tasks: list, period: str, project_filter: str = None) -> str:
    if project_filter:
        tasks = [t for t in tasks if t.project_name.lower() == project_filter.lower()]
        period = f"{period} in '{project_filter}'"
    
    if not tasks:
        return f"No completed tasks {period}."
    
    by_project = defaultdict(list)
    for task in tasks:
        by_project[task.project_name].append(task)
    
    lines = [f"Completed {period}: {len(tasks)} tasks\n"]
    
    for project, project_tasks in sorted(by_project.items()):
        lines.append(f"\n{project} ({len(project_tasks)}):")
        for task in project_tasks:
            lines.append(f"  - {task.content}")
    
    return "\n".join(lines)


def format_pending_tasks(tasks: list, project_filter: str = None) -> str:
    if project_filter:
        tasks = [t for t in tasks if t.project_name.lower() == project_filter.lower()]
    
    if not tasks:
        msg = f"No active tasks in '{project_filter}'." if project_filter else "No active tasks. Nice!"
        return msg
    
    by_project = defaultdict(list)
    for task in tasks:
        by_project[task.project_name].append(task)
    
    lines = [f"Active tasks: {len(tasks)}\n"]
    
    for project, project_tasks in sorted(by_project.items()):
        lines.append(f"\n{project} ({len(project_tasks)}):")
        for task in project_tasks:
            due = f" [due: {task.due_date}]" if task.due_date else ""
            lines.append(f"  - {task.content}{due}")
    
    return "\n".join(lines)


@router.message(Command("projects"))
async def cmd_projects(message: Message):
    client = await get_client(message)
    if not client:
        return
    
    projects = await client.get_projects()
    if not projects:
        await message.answer("No projects found.")
        return
    
    lines = ["Your projects:\n"]
    for project_id, name in sorted(projects.items(), key=lambda x: x[1]):
        lines.append(f"  - {name}")
    
    lines.append("\nUse project name with commands:")
    lines.append("/today Work")
    lines.append("/week Personal")
    
    await message.answer("\n".join(lines))


@router.message(Command("today"))
async def cmd_today(message: Message, command: CommandObject):
    client = await get_client(message)
    if not client:
        return
    
    project_filter = command.args.strip() if command.args else None
    
    await message.answer("Fetching today's tasks...")
    tasks = await client.get_today_completed()
    report = format_tasks_report(tasks, "today", project_filter)
    await message.answer(report)


@router.message(Command("week"))
async def cmd_week(message: Message, command: CommandObject):
    client = await get_client(message)
    if not client:
        return
    
    project_filter = command.args.strip() if command.args else None
    
    await message.answer("Fetching this week's tasks...")
    tasks = await client.get_week_completed()
    report = format_tasks_report(tasks, "this week", project_filter)
    await message.answer(report)


@router.message(Command("month"))
async def cmd_month(message: Message, command: CommandObject):
    client = await get_client(message)
    if not client:
        return
    
    project_filter = command.args.strip() if command.args else None
    
    await message.answer("Fetching this month's tasks...")
    tasks = await client.get_month_completed()
    report = format_tasks_report(tasks, "this month", project_filter)
    await message.answer(report)


@router.message(Command("pending"))
async def cmd_pending(message: Message, command: CommandObject):
    client = await get_client(message)
    if not client:
        return
    
    project_filter = command.args.strip() if command.args else None
    
    await message.answer("Fetching active tasks...")
    tasks = await client.get_active_tasks()
    report = format_pending_tasks(tasks, project_filter)
    await message.answer(report)
