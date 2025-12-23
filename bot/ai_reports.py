import aiohttp
from typing import Optional
import os
from datetime import datetime


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

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

DEFAULT_MONTHLY_PROMPT = """Сформируй месячный отчёт на основе списка задач. Используй такой формат и стилистику:

Пример моего отчёта:
---
Отчет за ноябрь 2025

643. SeaLinkTrack (https://ovsapp.atlassian.net/browse/WAD-638) - Сделал функционал, ушло на релиз

376. SocialTrackerX (ссылка) - Доработака функционала, онбординг и пр, ушло на релиз

MuseAIPro (ссылка) - предрелизная подготовка + ушло на релиз

———————

Взял в работу 572. ClearTapStudio (ссылка) - сделал весь функционал и прочее, на днях уйдет на релиз

Взял в работу 716. RareCoinsAI (ссылка) - сделал весь функционал, UI и прочее, сейчас на стадии тестов

——————

Занимался АБ тестами: сделал для NFC Orbit (ссылка) и Kaledoscope (ссылка) Dreams
---

Правила:
- Начни с "Отчет за [месяц год]"
- Группируй по смыслу: завершённые проекты, взятые в работу, другие активности
- Разделяй группы линией ———————
- Если есть ссылки в задачах - сохрани их
- Пиши кратко, по делу
- НЕ используй markdown (**, *, ` и т.д.)

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
