import asyncio

from configuration.environment import scheduler, dp, bot
from routers.base import base
from routers.fetch_images.config_commands import fetch_config
from routers.fetch_images.fetch_media import fetch_media

from routers.lifecycle import lifecycle
from configuration.logging import setup_logging


async def main():
    setup_logging()
    scheduler.start()

    dp.include_routers(fetch_media, fetch_config, base, lifecycle)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
