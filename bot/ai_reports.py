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


def get_report_header(report_type: str) -> str:
    """Генерирует заголовок отчёта с правильной датой"""
    now = datetime.now()
    
    if report_type == "daily":
        return f"Привет, отчет {now.day}.{now.month}\n\n"
    else:
        months = ["январь", "февраль", "март", "апрель", "май", "июнь",
                  "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
        
        if now.day <= 5:
            if now.month == 1:
                month_name = months[11]
                year = now.year - 1
            else:
                month_name = months[now.month - 2]
                year = now.year
        else:
            month_name = months[now.month - 1]
            year = now.year
        
        return f"Отчет за {month_name} {year}\n\n"

DEFAULT_DAILY_PROMPT = """Сформируй дневной отчёт на основе списка задач. НЕ ПИШИ заголовок с датой - только содержимое.

ВАЖНО: Объединяй ВСЕ задачи одного проекта в ОДНУ строку!

ВАЖНО про ссылки:
Если в названии проекта есть ссылка в скобках, например: "719. MirrorBeam (https://link.com)"
То сделай название кликабельным в HTML формате: <a href="https://link.com">719. MirrorBeam</a>

Пример входа:
- Добил UI (проект: 719. MirrorBeam (https://link.com))
- Отправил на онборды (проект: 719. MirrorBeam (https://link.com))
- Проверил баги (проект: 680. GroupFusion)

Пример выхода:
<a href="https://link.com">719. MirrorBeam</a> (6 ч): Добил UI, отправил на онборды, протестировал на телевизоре

680. GroupFusion (2 ч): Проверил баги, отправил на ASO

Правила:
- НЕ пиши "Привет, отчет..." - это добавится автоматически
- ГРУППИРУЙ все задачи одного проекта В ОДНУ СТРОКУ через запятую
- Не повторяй название проекта несколько раз
- Оцени общее время на проект (сумма по всем задачам)
- Пиши кратко, по делу
- НЕ используй markdown (**, *, `)
- Используй HTML только для ссылок: <a href="url">текст</a>

Задачи:
{tasks}"""

DEFAULT_MONTHLY_PROMPT = """Проанализируй список задач за месяц и сделай КРАТКУЮ ВЫЖИМКУ по каждому проекту.

НЕ перечисляй все задачи! Сделай осмысленное резюме что было сделано и определи стадию проекта.

Стадии проектов:
- "ушёл на релиз" - если видишь задачи про релиз, отправку в стор, финальные правки
- "на стадии тестов" - если видишь задачи про тесты, дебаг, фикс багов
- "в активной разработке" - если видишь задачи про функционал, UI, фичи
- "взят в работу" - если только начальные задачи

ВАЖНО про ссылки:
Если в названии проекта есть ссылка в скобках, сделай название кликабельным:
<a href="https://link.com">719. MirrorBeam</a>

Пример входа:
- Добил UI (проект: 719. MirrorBeam (https://link.com))
- Хромакаст фичи (проект: 719. MirrorBeam (https://link.com))
- Отправил на онборды (проект: 719. MirrorBeam (https://link.com))
- Релиз в стор (проект: 719. MirrorBeam (https://link.com))
- Сделал функционал X (проект: 680. GroupFusion)
- Начал тесты (проект: 680. GroupFusion)

Пример ПРАВИЛЬНОГО выхода:
<a href="https://link.com">719. MirrorBeam</a> - Добил UI, сделал хромакаст фичи, отправил на онборды. Ушёл на релиз

680. GroupFusion - Сделал основной функционал. На стадии тестов

Правила:
- НЕ пиши "Отчет за..." - заголовок добавится автоматически
- ОДНА строка на проект с КРАТКИМ резюме
- В конце строки - стадия проекта
- НЕ перечисляй каждую задачу отдельно
- НЕ используй markdown (**, *, `)
- Используй HTML только для ссылок: <a href="url">текст</a>

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
                        header = get_report_header(report_type)
                        return header + text
                
                return None
    except Exception as e:
        print(f"Gemini API exception: {e}")
        return None
