from aiogram import Router

from bot.handlers import start, reports, tasks

router = Router()
router.include_router(start.router)
router.include_router(reports.router)
router.include_router(tasks.router)
