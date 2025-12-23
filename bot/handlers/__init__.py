from aiogram import Router

from bot.handlers import start, menu

router = Router()
router.include_router(start.router)
router.include_router(menu.router)
