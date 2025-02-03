import logging
from io import BytesIO
from typing import Union

import aiohttp
from PIL import Image

async def resize_problematic_image(image_url: str) -> Union[BytesIO, None]:
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status != 200:
                logging.warning(f"Ошибка при загрузке изображения: {response.status}")
                return None

            image_data = await response.read()

            if not image_data:
                logging.warning("Пустой респонс.")
                return None

            image = Image.open(BytesIO(image_data))

            max_size = (1280, 1280)
            image.thumbnail(max_size)

            image_byte_data = BytesIO()
            image.save(image_byte_data, format='PNG')
            image_byte_data.seek(0)

            return image_byte_data
