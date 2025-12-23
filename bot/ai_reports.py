import aiohttp
from typing import Optional, List
import os
from datetime import datetime


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

EXCLUDE_PROJECTS = os.getenv("EXCLUDE_PROJECTS", "Inbox,Список желаний").split(",")


def filter_work_tasks(tasks: list) -> list:
    """Фильтрует задачи, исключая личные проекты"""
    exclude = [p.strip().lower() for p in EXCLUDE_PROJECTS]
    return [t for t in tasks if t.project_name.lower() not in exclude]

DEFAULT_DAILY_PROMPT = """Сформируй дневной отчёт на основе списка задач. Используй ТОЧНО такой формат и стилистику:

Пример моего отчёта:
---
Привет, отчет 6.11

572. ClearTap Studio (https://ovsapp.atlassian.net/browse/WAD-536) (5 ч): Доработал редирект, сделал гайд, настройки, + фикс разных некритичных багов. Закончил с разработкой

376. SocialTrackerX (https://ovsapp.atlassian.net/jira/core/projects/WAD/board) (3 ч): Занимался первым дебагом - подправил UI в паре мест, улучшил обработку ошибок для АИ, и внес фикс в работу скриптов, тестил на акке с 3к+ подписчиками - все отработало, отправил на ретест
---

Правила:
- Начни с "Привет, отчет [сегодняшняя дата в формате Д.М]"
- Каждый проект с новой строки
- Формат: Номер. Название (ссылка если есть) (часы): что сделал
- Пиши кратко, по делу, неформально
- Если есть ссылки в задачах - сохрани их
- НЕ используй markdown (**, *, ` и т.д.)
- Оцени примерно часы на каждый проект

Задачи:
{tasks}"""

DEFAULT_MONTHLY_PROMPT = """Сформируй месячный отчёт на основе списка задач.

Пример формата:
---
Отчет за декабрь 2025

719. MirrorBeam - Добил UI, хромакаст фичи и пр, ушло на релиз

———————

Взял в работу ClearTapStudio - сделал весь функционал, UI, на стадии тестов

———————

Занимался АБ тестами для NFC Orbit и Kaleidoscope
---

Правила:
- Определи текущий месяц и год сам
- Группируй задачи по проектам
- Если задача относится к завершённому проекту - пиши что ушло на релиз
- Если проект в работе - пиши статус
- Разделяй смысловые блоки линией ———————
- Если какой-то категории нет (например нет АБ тестов) - просто не пиши её, не оставляй пустые секции
- НЕ используй квадратные скобки [] и плейсхолдеры
- НЕ используй markdown (**, *, `)
- Пиши конкретно что сделано, без воды

Задачи:
{tasks}"""


def get_daily_prompt() -> str:
    return os.getenv("DAILY_REPORT_PROMPT", DEFAULT_DAILY_PROMPT)


def get_monthly_prompt() -> str:
    return os.getenv("MONTHLY_REPORT_PROMPT", DEFAULT_MONTHLY_PROMPT)


async def generate_report(tasks_text: str, report_type: str = "daily") -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    
    if report_type == "daily":
        prompt_template = get_daily_prompt()
    else:
        prompt_template = get_monthly_prompt()
    
    prompt = prompt_template.replace("{tasks}", tasks_text)
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    print(f"Gemini API error: {error}")
                    return None
                
                data = await resp.json()
                
                candidates = data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        text = parts[0].get("text", "")
                        text = text.replace("**", "").replace("`", "")
                        return text
                
                return None
    except Exception as e:
        print(f"Gemini API exception: {e}")
        return None
