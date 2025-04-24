import asyncio
import logging
from datetime import datetime

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile
from aiohttp import ClientSession
from peewee import Query

from database.models import TagsArchive, PostIds, UrlQueue
from handlers.fetch_images.send_attachment import AttachmentType, get_send_command, send_attachment
from utils.queue import dequeue_and_get_urls
from utils.resize_image import resize_problematic_image
from utils.update_database import update_database

fetch_and_send = Router()

async def fetch_and_send_media() -> None:
    async with ClientSession() as session:
        chat_ids: Query = TagsArchive.select(TagsArchive.chat_id).distinct()
        chat_id_list: list[int] = [int(chat_id.chat_id) for chat_id in chat_ids]

        for chat_id in chat_id_list:
            urls = dequeue_and_get_urls(chat_id)
            if not urls:
                continue

            for url_record in urls:
                url = url_record.url
                tag = url_record.tag
                logging.info(f"Запрос к Danbooru: {url}")
                await asyncio.sleep(1)

                async with session.get(url) as response:
                    if response.status != 200:
                        logging.error(f'Ошибка запроса {url}, статус {response.status}')
                        UrlQueue.update(status=0).where(
                            UrlQueue.chat_id == chat_id,
                            UrlQueue.url == url
                        ).execute()
                        logging.info('response != 200')
                        continue

                    data = await response.json()
                    if not data:
                        logging.info('not data')
                        continue

                post_ids: Query = PostIds.select().where(PostIds.chat_id == chat_id)
                post_lst: list[int] = []

                for post_id in post_ids:
                    post_lst.append(int(post_id.post_id))

                # В респонсе приходят изображения от нового (0) к старому (19)
                for post in data[::-1]:
                    iso_post_date: datetime = datetime.fromisoformat(post['created_at'])
                    formatted_post_date: str = str(iso_post_date.strftime("%Y-%m-%dT%H:%M:%S"))

                    if 'file_url' not in post or int(post['id']) in post_lst:
                        logging.warning(
                            f"Пост {post['id']} пропущен"
                        )
                        continue

                    try:
                        command = get_send_command(post, chat_id)

                        if not command:
                            logging.info('not command')
                            continue

                        await send_attachment(command)
                        # Задержка, чтобы избежать спам-алертов
                        await asyncio.sleep(2)

                    except TelegramBadRequest as error:
                        logging.info(error)

                        if command.attachmentType == AttachmentType.PHOTO:
                            logging.info("Меняем размер проблемного изображения")
                            if isinstance(command.file, str):
                                image_url_to_resize: str = command.file
                                resized_image = await resize_problematic_image(image_url_to_resize)
                                if resized_image:
                                    try:
                                        image_bytes = resized_image.getvalue()
                                        command.file = BufferedInputFile(file=image_bytes,
                                                                         filename="resized_image.jpg")
                                        await send_attachment(command)
                                        # Задержка, чтобы избежать спам-алертов
                                        await asyncio.sleep(2)

                                    except TelegramBadRequest as resize_error:
                                        logging.error(
                                            f"Ошибка при отправке ресайзнутого изображения: {resize_error}")

                                else:
                                    logging.error("None пришёл от resize_image")
                            else:
                                logging.error("Тип не не является строкой")

                logging.info(f"Обновление базы данных для чата {chat_id} и тега {tag}")
                await update_database(chat_id, tag, post, formatted_post_date, url)
