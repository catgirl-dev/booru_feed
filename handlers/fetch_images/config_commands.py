import logging
from datetime import datetime, timezone, timedelta

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from configuration.environment import scheduler
from database.models import IntervalConfig, TagsArchive, CensorStatus
from filters.is_admin import IsAdmin
from filters.is_group import ChatTypeFilter
from handlers.fetch_images.fetch_media import fetch_and_send_media
from utils.queue import enqueue_urls

fetch_config = Router()


@fetch_config.message(Command('start_fetch'), ChatTypeFilter(), IsAdmin())
async def start_fetch(message: Message):
    logging_user_id = message.from_user.id
    logging.info(f'Бот запущен пользователем с ID: {logging_user_id}')

    try:
        interval, created = IntervalConfig.get_or_create(
            chat_id=message.chat.id,
            defaults={'time': 30}
        )
    except Exception as e:
        logging.error(f"Ошибка при создании интервала: {e}")
        await message.reply('Ошибка при запуске бота')
        return

    try:
        CensorStatus.get_or_create(
            chat_id=message.chat.id,
            defaults={'status': 1}
        )
    except Exception as e:
        logging.error(f"Ошибка при создании CensorStatus: {e}")
        await message.reply('Ошибка при запуске бота')
        return

    existing_job = scheduler.get_job(f'fetch_media_{message.chat.id}')
    if existing_job:
        await message.reply('Бот уже запущен.')
        return

    try:
        time = int(str(interval.time))

        scheduler.add_job(
            fetch_and_send_media, 'interval',
            minutes=time, id=f'fetch_media_{message.chat.id}'
        )
    except Exception as e:
        logging.error(f"Ошибка при создании джоба на отправку медиа{e}")

    try:
        existing_queue = scheduler.get_job(f'enqueue_urls_{message.chat.id}')
        if existing_queue:
            return
        else:
            scheduler.add_job(
                enqueue_urls, 'interval', seconds=15, id=f'enqueue_urls_{message.chat.id}'
            )
    except Exception as e:
        logging.error(f"Ошибка при добавлении джоба очереди {e}")

    await message.reply(
        f'Поиск новых медиа начат! Каждые {time} минут(ы) '
        f'я буду искать новые изображения и отправлять их в чат.'
    )


@fetch_config.message(Command('stop_fetch'), ChatTypeFilter(), IsAdmin())
async def stop_fetch(message: Message):
    job_id = f'fetch_media_{message.chat.id}'
    existing_job = scheduler.get_job(job_id)

    if not existing_job:
        await message.reply('Поиск медиа не был запущен для этого чата.')
        return

    scheduler.remove_job(job_id)

    await message.reply('Поиск новых медиа будет остановлен.')


@fetch_config.message(Command('show_tags'), ChatTypeFilter(), IsAdmin())
async def show_tags(message: Message):
    tags = TagsArchive.select().where(TagsArchive.chat_id == message.chat.id)

    if not tags:
        await message.reply(
            'Список тегов пуст! Вы можете добавить теги '
            'командой /add_tag. Напишите её и укажите теги. '
            'Можно указать один тег или много — через пробел.'
        )
        return

    tag_list = ''

    for tag in tags:
        tag_list += str(tag.tag) + ' '

    await message.reply(
        f'Список тегов для данного чата: \n```\n{tag_list}\n```',
        parse_mode='Markdown'
    )


@fetch_config.message(Command('add_tag'), ChatTypeFilter(), IsAdmin())
async def add_tag(message: Message, command: CommandObject):
    command_args: str = command.args

    if not command_args:
        await message.reply(
            'Пожалуйста, введите хотя бы один тег!'
        )
        return

    tags_to_add = command_args.strip().split(' ')

    for tag in tags_to_add:
        existing_tag = TagsArchive.select().where(
            TagsArchive.chat_id == message.chat.id,
            TagsArchive.tag == tag
        )

        if existing_tag:
            await message.reply(
                f'Тег *{tag}* уже существует в базе данных!',
                parse_mode='Markdown'
            )
            return

        TagsArchive.create(
            chat_id=message.chat.id,
            tag=tag,
            last_post_date=datetime.now(timezone(timedelta(hours=-5))).strftime("%Y-%m-%dT%H:%M:%S")
        )

    await message.reply(
        f'Следующие теги были успешно добавлены: '
        f'{", ".join([f"*{tag}*" for tag in tags_to_add])}',
        parse_mode='Markdown'
    )


@fetch_config.message(Command('remove_tag'), ChatTypeFilter(), IsAdmin())
async def remove_tag(message: Message, command: CommandObject):
    command_args: str = command.args

    if not command_args:
        await message.reply(
            'Пожалуйста, введите хотя бы один тег!'
        )
        return

    tags_to_remove = command_args.strip().split()

    for tag in tags_to_remove:
        existing_tag = TagsArchive.select().where(
            TagsArchive.chat_id == message.chat.id,
            TagsArchive.tag == tag
        )

        if not existing_tag:
            await message.reply(
                f'Тега *{tag}* нет в базе данных!',
                parse_mode='Markdown'
            )
            return

        remove_pattern = TagsArchive.delete().where(
            TagsArchive.tag == tag,
            TagsArchive.chat_id == message.chat.id)
        remove_pattern.execute()

    await message.reply(
        f'Следующие теги были успешно удалены: '
        f'{", ".join([f"*{tag}*" for tag in tags_to_remove])}',
        parse_mode='Markdown'
    )

@fetch_config.message(Command('censor_status'), ChatTypeFilter(), IsAdmin())
async def censor_status(message: Message, command: CommandObject):
    command_args: str = command.args
    chat_id: int = message.chat.id

    if not command_args or command_args not in ['0', '1', '2']:
        await message.reply(
            'Пожалуйста, укажите 1 (включить цензуру) или 0 (выключить цензуру).'
            'Пример для выключения цензуры: /censor_status 0'
        )
        logging.error('Цензура указана неправильно')
        return

    status_value = int(command_args)

    if status_value == 0:
        CensorStatus.update(status=status_value).where(CensorStatus.chat_id == chat_id).execute()
        await message.reply('Цензура выключена.')

    elif status_value == 1:
        CensorStatus.update(status=status_value).where(CensorStatus.chat_id == chat_id).execute()
        await message.reply('Цензура включена.')

    elif status_value == 2:
        CensorStatus.update(status=status_value).where(CensorStatus.chat_id == chat_id).execute()
        await message.reply('Поиск изображений с рейтингом 18+ выключен.')



@fetch_config.message(Command('change_interval'), ChatTypeFilter(), IsAdmin())
async def change_interval(message: Message, command: CommandObject):
    command_args: str = command.args

    if not command_args or not command_args.isdigit() or command_args == '0':
        await message.reply(
            'Пожалуйста, укажите интервал целым положительным числовым значением (в минутах). '
            'Число не может равняться нулю. Дробным тоже не может. Ну и комплексным, наверное, тоже.'
            'Пример для интервала 10 минут: /change_interval 10'
        )
        return

    new_interval = int(command_args)
    if new_interval is None:
        logging.error("warning! null new_interval")

    interval, created = IntervalConfig.get_or_create(chat_id=message.chat.id)
    interval.time = new_interval
    interval.save()

    existing_job = scheduler.get_job(f'fetch_media_{message.chat.id}')
    if existing_job:
        existing_job.remove()

    scheduler.add_job(
        fetch_and_send_media, 'interval',
        minutes=new_interval,
        id=f'fetch_media_{message.chat.id}'
    )

    await message.reply(
        f'Интервал обновлен! '
        f'Теперь я буду искать новые изображения каждые {new_interval} минут(ы).'
    )
