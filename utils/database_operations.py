import logging
from typing import List

from database.models import TagsArchive, PostIds, UrlQueue


def get_chat_ids() -> List[int]:
    chat_ids = TagsArchive.select(TagsArchive.chat_id).distinct()
    chat_id_list: list[int] = [int(chat_id.chat_id) for chat_id in chat_ids]
    return chat_id_list


async def update_database(chat_id: int, tag, post, formatted_post_date: str, url: str) -> None:
    try:
        existing_tag = TagsArchive.get_or_none(
            TagsArchive.chat_id == chat_id,
            TagsArchive.tag == tag
        )

        if not existing_tag:
            logging.error('Не существует записи для тега в БД')
            return

        TagsArchive.update(last_post_date=formatted_post_date).where(
            TagsArchive.chat_id == chat_id,
            TagsArchive.tag == tag
        ).execute()
        logging.info('Обновление даты в бд')

        post_id = int(post['id'])
        logging.info(post_id)
        existing_post_id = PostIds.get_or_none(
            PostIds.chat_id == chat_id,
            PostIds.post_id == post_id
        )

        if not existing_post_id:
            PostIds.create(chat_id=chat_id, post_id=post_id)
            logging.info(f'Пост ID {post_id} занесён в БД')
        else:
            logging.info(f'Пост ID {post_id} уже существует в базе.')

        existing_url = UrlQueue.get_or_none(
            UrlQueue.chat_id == chat_id,
            UrlQueue.url == url
        )

        if existing_url:
            UrlQueue.delete().where(
                UrlQueue.chat_id == chat_id,
                UrlQueue.url == url
            ).execute()
            logging.info(f'URL {url} удалён из очереди')

    except Exception as e:
        logging.error(f'Ошибка при обновлении базы данных: {e}')
