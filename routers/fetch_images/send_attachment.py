import logging
from enum import Enum
from typing import Union

from aiogram.types import InputFile

from configuration.environment import bot
from database.models import CensorStatus


class AttachmentType(Enum):
    VIDEO = 1
    GIF = 2
    PHOTO = 3


class SendAttachCommand:
    def __init__(self, attachment_type: AttachmentType, file: Union[InputFile, str], has_spoiler: bool, chat_id: any):
        self.attachmentType = attachment_type
        self.file = file
        self.has_spoiler = has_spoiler
        self.chat_id = chat_id


def get_send_command(post: any, chat_id: any) -> Union[SendAttachCommand, None]:
    censor_status_found = CensorStatus.select().where(CensorStatus.chat_id == chat_id).first()

    if not censor_status_found:
        logging.error('Не получен статус цензуры для чата')
        return None

    current_censor_status = int(str(censor_status_found.status))

    if post['file_ext'] == 'gif':
        att_type = AttachmentType.GIF
    elif post['file_ext'] in ['mp4', 'webm', 'ogv']:
        att_type = AttachmentType.VIDEO
    else:
        att_type = AttachmentType.PHOTO

    if current_censor_status == 1:
        # Questionable (q), Explicit (e), Sensitive (s)
        hs = post['rating'] in ['q', 'e', 's']
    elif current_censor_status == 0:
        hs = False
    else:
        logging.info('Выключен поиск 18+')
        return None

    return SendAttachCommand(att_type, post['file_url'], hs, chat_id)


async def send_attachment(command: SendAttachCommand):
    match command.attachmentType:
        case(AttachmentType.VIDEO):
            await bot.send_video(
                chat_id=command.chat_id,
                video=command.file,
                has_spoiler=command.has_spoiler,
            )
        case(AttachmentType.GIF):
            await bot.send_animation(
                chat_id=command.chat_id,
                gif=command.file,
                has_spoiler=command.has_spoiler,
            )
        case(AttachmentType.PHOTO):
            await bot.send_photo(
                chat_id=command.chat_id,
                photo=command.file,
                has_spoiler=command.has_spoiler,
            )
