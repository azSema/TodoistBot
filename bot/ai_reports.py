import aiohttp
from typing import Optional
import os


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

DEFAULT_DAILY_PROMPT = """Ты помощник по анализу продуктивности. Проанализируй список выполненных задач за день и сделай краткий отчёт на русском языке.

Формат отчёта:
1. Сколько задач выполнено
2. По каким проектам работал
3. Основные достижения дня
4. Краткий вывод (1-2 предложения)

Будь кратким и конкретным. Максимум 200 слов.

Задачи:
{tasks}"""

DEFAULT_MONTHLY_PROMPT = """Ты помощник по анализу продуктивности. Проанализируй список выполненных задач за месяц и сделай отчёт на русском языке.

Формат отчёта:
1. Общая статистика (количество задач, проекты)
2. Ключевые достижения месяца
3. Какие направления были в приоритете
4. Рекомендации на следующий месяц

Будь структурированным. Максимум 400 слов.

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
                        return parts[0].get("text", "")
                
                return None
    except Exception as e:
        print(f"Gemini API exception: {e}")
        return None
