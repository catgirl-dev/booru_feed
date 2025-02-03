from peewee import SqliteDatabase, Model, IntegerField, CharField

db = SqliteDatabase('database/fetcher_info.db')


class TagsArchive(Model):
    chat_id = IntegerField()
    tag = CharField()
    last_post_date = CharField()

    class Meta:
        database = db


class IntervalConfig(Model):
    chat_id = IntegerField()
    time = IntegerField()

    class Meta:
        database = db


class PostIds(Model):
    chat_id = IntegerField()
    post_id = IntegerField()

    class Meta:
        database = db


class CensorStatus(Model):
    chat_id = IntegerField()
    status = IntegerField() # по умолчанию цензура включена (1)

    class Meta:
        database = db


class UrlQueue(Model):
    chat_id = IntegerField()
    url = CharField()
    status = IntegerField(default=0)  # 0 — в очереди, 1 — в обработке, выполнили — удаляем

    class Meta:
        database = db
