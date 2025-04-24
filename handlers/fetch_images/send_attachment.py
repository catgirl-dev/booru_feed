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


class CensorLevel(Enum):
    NO_CENSOR = 0
    PARTIAL_CENSOR = 1
    FULL_CENSOR = 2


def get_send_command(post: any, chat_id: any) -> Union[SendAttachCommand, None]:
    try:
        censor_status_found = CensorStatus.select().where(CensorStatus.chat_id == chat_id).first()
    except Exception as e:
        logging.error(f"Ошибка при попытке получить статус цензуры{e}")
        return None

    if not censor_status_found:
        logging.error('Не получен статус цензуры для чата')
        return None

    current_censor_status = CensorLevel(censor_status_found.status) # привожу к Enum

    if post['file_ext'] == 'gif':
        att_type = AttachmentType.GIF
    elif post['file_ext'] in ['mp4', 'webm', 'ogv']:
        att_type = AttachmentType.VIDEO
    elif post['file_ext'] in ['png', 'jpg', 'jpeg']:
        att_type = AttachmentType.PHOTO
    else:
        logging.info(f"Некорректный формат: {post['file_ext']}")
        return None

    # Questionable (q), Explicit (e), Sensitive (s)
    censored_ratings = {'q', 'e', 's'}
    has_spoiler: bool = False

    if current_censor_status == CensorLevel.PARTIAL_CENSOR:
        has_spoiler = post['rating'] in censored_ratings
    elif current_censor_status == CensorLevel.NO_CENSOR:
        has_spoiler = False
    elif current_censor_status == CensorLevel.FULL_CENSOR:
        if post['rating'] in censored_ratings:
            logging.info("Пост 18+ не будет отправлен")
            return None
        has_spoiler = False

    return SendAttachCommand(att_type, post['file_url'], has_spoiler, chat_id)


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
