import asyncio
import logging

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest

from database.models import PostIds
from handlers.fetch_images.send_attachment import get_send_command, send_attachment
from utils.database_operations import update_database, get_chat_ids
from utils.fetch_media_utils import construct_url, construct_isoformat_date, fetch_url_data, \
    handle_image_resize_error
from utils.queue import dequeue_and_get_urls

fetch_and_send = Router()


async def fetch_and_send_media() -> None:
    chat_id_list = get_chat_ids()

    for chat_id in chat_id_list:
        urls = dequeue_and_get_urls(chat_id)
        if not urls:
            continue

        for url in urls:
            url, tag = await construct_url(url)
            data = await fetch_url_data(url, chat_id)
            if not data:
                continue

            post_ids = PostIds.select().where(PostIds.chat_id == chat_id)
            post_lst: list[int] = []
            for post_id in post_ids:
                post_lst.append(int(post_id.post_id))

            # В респонсе приходят изображения от нового (0) к старому (19)
            for post in data[::-1]:
                formatted_post_date = construct_isoformat_date(post)

                # Пропускаем посты, которые уже были отправлены по другим тегам, чтобы избежать повторов
                if 'file_url' not in post or int(post['id']) in post_lst:
                    logging.warning(
                        f"Пост {post['id']} пропущен"
                    )
                    continue

                try:
                    command = get_send_command(post, chat_id)
                    if not command:
                        logging.info('Not command')
                        continue
                    await send_attachment(command)
                    # Задержка, чтобы избежать спам-алертов
                    await asyncio.sleep(2)
                except TelegramBadRequest as error:
                    await handle_image_resize_error(command, error)

            await update_database(chat_id, tag, post, formatted_post_date, url)
            logging.info(f"Обновлена база данных для чата {chat_id} и тега {tag}")
