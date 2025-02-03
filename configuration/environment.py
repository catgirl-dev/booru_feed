import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from configuration.scheduler import create_scheduler

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    exit('Пожалуйста укажите BOT_TOKEN в переменной окружения')

bot = Bot(TOKEN)

dp = Dispatcher()
scheduler = create_scheduler()
