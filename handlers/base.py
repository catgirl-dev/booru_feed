from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from texts import help_msg

base = Router()


@base.message(Command('ping'))
async def ping(message: Message):
    await message.reply('pong!')


@base.message(Command('help'))
async def help_command(message: Message):
    await message.reply(
        help_msg.help_msg,
        parse_mode='Markdown',
        disable_web_page_preview=True)


@base.message(Command('start'))
async def start(message: Message):
    await message.reply(
        help_msg.help_msg,
        parse_mode='Markdown',
        disable_web_page_preview=True)