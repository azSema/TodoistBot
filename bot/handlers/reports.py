from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime
from collections import defaultdict

from bot.handlers.base import get_client
from bot.todoist_client import TaskInfo

router = Router()


def format_tasks_report(tasks: list[TaskInfo], period: str) -> str:
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


def format_pending_tasks(tasks: list[TaskInfo]) -> str:
    if not tasks:
        return "No active tasks. Nice!"
    
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


@router.message(Command("today"))
async def cmd_today(message: Message):
    client = await get_client(message)
    if not client:
        return
    
    await message.answer("Fetching today's tasks...")
    tasks = await client.get_today_completed()
    report = format_tasks_report(tasks, "today")
    await message.answer(report)


@router.message(Command("week"))
async def cmd_week(message: Message):
    client = await get_client(message)
    if not client:
        return
    
    await message.answer("Fetching this week's tasks...")
    tasks = await client.get_week_completed()
    report = format_tasks_report(tasks, "this week")
    await message.answer(report)


@router.message(Command("month"))
async def cmd_month(message: Message):
    client = await get_client(message)
    if not client:
        return
    
    await message.answer("Fetching this month's tasks...")
    tasks = await client.get_month_completed()
    report = format_tasks_report(tasks, "this month")
    await message.answer(report)


@router.message(Command("pending"))
async def cmd_pending(message: Message):
    client = await get_client(message)
    if not client:
        return
    
    await message.answer("Fetching active tasks...")
    tasks = await client.get_active_tasks()
    report = format_pending_tasks(tasks)
    await message.answer(report)
