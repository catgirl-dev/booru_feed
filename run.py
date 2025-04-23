import asyncio

from configuration.environment import scheduler, dp, bot
from handlers.base import base
from handlers.fetch_images.config_commands import fetch_config
from handlers.fetch_images.fetch_media import fetch_and_send

from handlers.lifecycle import lifecycle
from configuration.logging import setup_logging


async def main():
    setup_logging()
    scheduler.start()

    dp.include_routers(fetch_and_send, fetch_config, base, lifecycle)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
