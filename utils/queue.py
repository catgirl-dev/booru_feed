import logging
from typing import List, Union

from peewee import Query

from database.models import UrlQueue


def enqueue_url(chat_id: int, url: str) -> None:
    try:
        #был Query
        existing_url: UrlQueue = UrlQueue.select().where(
            UrlQueue.chat_id == chat_id,
            UrlQueue.url == url
        ).first()

        if existing_url:
            logging.info(f'URL уже в очереди или обработан: {url}')

            '''
            Снова ставим в очередь URL, если его статус "в обработке"
            В dequeue условие status == 0 => если бот упадёт, URL будет проигнорирован
            '''

            if existing_url.status == 1:
                existing_url.status = 0
                existing_url.save()
                logging.info(f'URL восстановлен в очередь: {url}')
            return

        UrlQueue.create(chat_id=chat_id, url=url, status=0)
        logging.info(f'Новый URL добавлен в очередь: {url}')
    except Exception as e:
        logging.error(f'Ошибка при добавлении URL в очередь{e}')


def dequeue_and_get_url(chat_id: int) -> Union[List[str], None]:
    urls_from_db: list = list(UrlQueue.select().where(
        UrlQueue.chat_id == chat_id, UrlQueue.status == 0
    ))

    url_list: list[str] = []

    for url_from_db in urls_from_db:
        url = url_from_db.url
        url_list.append(url)

    # Меняем статус URL из очереди на "в обработке"
    if url_list:
        UrlQueue.update(status=1).where(
            UrlQueue.chat_id == chat_id,
            UrlQueue.url.in_(url_list)
        ).execute()

    return url_list
