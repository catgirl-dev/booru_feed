import asyncio
import logging
from datetime import datetime
from typing import Optional, Tuple

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile

from aiohttp import ClientSession

from database.models import UrlQueue
from handlers.fetch_images.send_attachment import AttachmentType, send_attachment
from utils.resize_image import resize_problematic_image


async def construct_url(url_record) -> Tuple[str, str]:
    url: str = url_record.url
    tag: str = url_record.tag
    logging.info(f"Запрос к Danbooru: {url}")
    await asyncio.sleep(1)
    return url, tag


def construct_isoformat_date(post) -> str:
    iso_post_date: datetime = datetime.fromisoformat(post['created_at'])
    formatted_post_date: str = str(iso_post_date.strftime("%Y-%m-%dT%H:%M:%S"))
    return formatted_post_date


async def fetch_url_data(url: str, chat_id: int) -> Optional[dict]:
    """ Отправляет для Данбуру запрос, получает ответ """
    async with ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logging.error(f'Ошибка запроса {url}, статус {response.status}')
                    UrlQueue.update(status=0).where(
                        UrlQueue.chat_id == chat_id,
                        UrlQueue.url == url
                    ).execute()
                    return None

                data = await response.json()
                return data if data else None
        except Exception as e:
            logging.error(f'Ошибка при получении данных: {e}')
            return None


async def handle_image_resize_error(command, error: TelegramBadRequest) -> None:
    """ Ресайзит изображение при ошибке отправки в Телеграм чат """
    logging.error(f"Ошибка при отправке медиафайла: {error}")

    if command.attachmentType != AttachmentType.PHOTO:
        return

    if not isinstance(command.file, str):
        logging.error("Тип не является строкой")
        return

    image_url_to_resize: str = command.file
    resized_image = await resize_problematic_image(image_url_to_resize)
    logging.info("Меняем размер проблемного изображения")

    if not resized_image:
        logging.error("None пришёл от resize_image")
        return

    try:
        image_bytes = resized_image.getvalue()
        command.file = BufferedInputFile(
            file=image_bytes,
            filename="resized_image.jpg"
        )
        await send_attachment(command)
        await asyncio.sleep(2)  # Задержка против спам-алертов
    except TelegramBadRequest as resize_error:
        logging.error(f"Ошибка при отправке ресайзнутого изображения: {resize_error}")
