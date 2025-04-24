import asyncio
import logging
from datetime import datetime
from typing import Iterable, Any, Optional, Tuple


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
