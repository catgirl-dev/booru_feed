from aiogram import Router

from database.models import db, TagsArchive, IntervalConfig, PostIds, CensorStatus, UrlQueue

lifecycle = Router()


@lifecycle.startup()
async def on_startup():
    db.connect()
    db.create_tables(
        [TagsArchive,
         IntervalConfig,
         PostIds,
         CensorStatus,
         UrlQueue]
    )


@lifecycle.shutdown()
async def on_shutdown():
    db.close()
