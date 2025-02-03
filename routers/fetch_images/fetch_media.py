import asyncio
import logging
from datetime import datetime

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile
from aiohttp import ClientSession
from peewee import Query

from database.models import TagsArchive, PostIds, UrlQueue

from routers.fetch_images.send_attachment import AttachmentType, get_send_command, send_attachment
from utils.queue import enqueue_url, dequeue_and_get_url
from utils.resize_image import resize_problematic_image

fetch_media = Router()

async def fetch_new_media():
    async with ClientSession() as session:
        chat_ids: Query = TagsArchive.select(TagsArchive.chat_id).distinct()

        chat_id_list: list[int] = [int(chat_id.chat_id) for chat_id in chat_ids]

        for chat_id in chat_id_list:
            tags: list = list(TagsArchive.select().where(TagsArchive.chat_id == chat_id))

            for tag in tags:
                url: str = (f'https://danbooru.donmai.us/posts.json?tags=date:>'
                       f'{str(tag.last_post_date)} {str(tag.tag)}')

                enqueue_url(chat_id, url)

            url_from_db: list[str] = dequeue_and_get_url(chat_id)

            for url in url_from_db:
                logging.info(url)
                # Задержка между запросами к Danbooru, чтобы избежать 429 статуса
                await asyncio.sleep(1)

                async with session.get(url) as response:
                    if response.status != 200:
                        logging.error(
                            f'Ошибка запроса к API для чата {chat_id}, статус {response.status}')

                        UrlQueue.update(
                            status=0).where(
                            UrlQueue.chat_id == chat_id,
                            UrlQueue.url == url
                        ).execute()
                        continue

                    data = await response.json()
                    if not data:
                        continue

                post_ids: Query = PostIds.select().where(PostIds.chat_id == chat_id)
                post_lst: list[int] = []

                for post_id in post_ids:
                    post_lst.append(int(post_id.post_id))

                # В респонсе приходят изображения от нового (0) к старому (19)
                for post in data[::-1]:
                    iso_post_date = datetime.fromisoformat(post['created_at'])
                    formatted_post_date = iso_post_date.strftime("%Y-%m-%dT%H:%M:%S")

                    if 'file_url' not in post or int(post['id']) in post_lst:
                        logging.warning(
                            f"Пост {post['id']} пропущен"
                        )
                        continue

                    try:
                        command = get_send_command(post, chat_id)

                        if not command:
                            continue

                        await send_attachment(command)
                        # Задержка, чтобы избежать спам-алертов
                        await asyncio.sleep(1)

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
                                    except TelegramBadRequest as resize_error:
                                        logging.error(
                                            f"Ошибка при отправке ресайзнутого изображения: {resize_error}")

                                else:
                                    logging.error("None пришёл от resize_image")
                            else:
                                logging.error("Тип не не является строкой")

                    existing_tag = TagsArchive.select().where(
                        TagsArchive.chat_id == chat_id,
                        TagsArchive.tag == tag.tag
                    ).first()

                    if not existing_tag:
                        logging.error('Не существует записи для тега в бд')
                        continue

                    TagsArchive.update(
                        last_post_date=formatted_post_date).where(
                        TagsArchive.chat_id == chat_id,
                        TagsArchive.tag == tag.tag
                    ).execute()

                    existing_post_id = PostIds.select().where(
                        PostIds.chat_id == chat_id,
                        PostIds.post_id == int(post['id'])
                    ).first()

                    if not existing_post_id:
                        PostIds.create(chat_id=chat_id, post_id=int(post['id']))
                        logging.info('Пост айди занесён в бд')
                    else:
                        logging.info(f'Пост с ID {post['id']} уже существует в базе.')

                    existing_url = UrlQueue.select().where(
                        UrlQueue.chat_id == chat_id,
                        UrlQueue.url == url
                    ).first()

                    if not existing_url:
                        continue

                    UrlQueue.delete().where(
                        UrlQueue.chat_id == chat_id,
                        UrlQueue.url == url
                    ).execute()