# Todoist Report Bot

Telegram бот для отчётов и управления задачами в Todoist.

## Возможности

- **Отчёты**: что сделал за день/неделю/месяц
- **Мультипользовательский**: каждый юзер подключает свой Todoist
- **Добавление задач**: прямо из Telegram

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Начало работы, подключение Todoist |
| `/today` | Задачи выполненные сегодня |
| `/week` | Задачи за неделю |
| `/month` | Задачи за месяц |
| `/pending` | Активные задачи |
| `/add <текст>` | Добавить задачу в Inbox |
| `/setkey` | Сменить Todoist API ключ |
| `/help` | Список команд |

## Установка

### 1. Создай Telegram бота

1. Открой @BotFather в Telegram
2. Отправь `/newbot`
3. Следуй инструкциям, получи токен

### 2. Установи зависимости

```bash
cd TodoistBot
pip install -r requirements.txt
```

### 3. Настрой конфиг

```bash
cp .env.example .env
```

Открой `.env` и вставь токен бота:
```
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 4. Запусти

```bash
python run.py
```

## Как юзеры подключают Todoist

1. Юзер открывает бота, жмёт `/start`
2. Бот просит API токен от Todoist
3. Юзер идёт на todoist.com/prefs/integrations
4. Копирует API token и отправляет боту
5. Готово!

## Как добавить новую команду

1. Создай файл в `bot/handlers/`, например `stats.py`:

```python
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from bot.handlers.base import get_client

router = Router()

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    client = await get_client(message)
    if not client:
        return
    
    # твоя логика
    await message.answer("Your stats...")
```

2. Добавь в `bot/handlers/__init__.py`:

```python
from bot.handlers import start, reports, tasks, stats  # добавь stats

router = Router()
router.include_router(start.router)
router.include_router(reports.router)
router.include_router(tasks.router)
router.include_router(stats.router)  # добавь эту строку
```

3. Готово!

## Деплой

### Railway / Render

1. Запушь код на GitHub
2. Подключи репо к Railway/Render
3. Добавь переменную `BOT_TOKEN`
4. Деплой автоматом

### VPS

```bash
# Установи screen для фона
screen -S todoistbot
python run.py
# Ctrl+A, D для отсоединения
```

## Структура проекта

```
TodoistBot/
├── bot/
│   ├── handlers/       # Команды бота
│   │   ├── start.py    # /start, /setkey, /help
│   │   ├── reports.py  # /today, /week, /month, /pending  
│   │   └── tasks.py    # /add
│   ├── config.py       # Конфигурация
│   ├── database.py     # SQLite для юзеров
│   ├── todoist_client.py # Todoist API
│   └── main.py         # Точка входа
├── run.py
├── requirements.txt
└── .env
```
