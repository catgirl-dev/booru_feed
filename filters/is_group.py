from aiogram.filters import BaseFilter
from aiogram.types import Message


class ChatTypeFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply('Чтобы начать пользоваться ботом, добавьте его в чат '
                                'и напишите /start_fetch')
            return False
        return True
