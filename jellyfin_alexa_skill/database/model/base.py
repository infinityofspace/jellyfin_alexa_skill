from peewee import Model, SqliteDatabase

db = SqliteDatabase(None)


class BaseModel(Model):
    class Meta:
        database = db
