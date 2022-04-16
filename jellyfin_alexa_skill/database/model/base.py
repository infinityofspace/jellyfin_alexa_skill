from enum import Enum
from typing import Type

from peewee import Model, SqliteDatabase, Field

db = SqliteDatabase(None)


class BaseModel(Model):
    class Meta:
        database = db


class CharEnumField(Field):
    """
    Database field for storing enumeration as char field.
    """

    field_type = "char"

    def __init__(self, enum_class: Type[Enum], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.enum_class = enum_class

    def db_value(self, value):
        return value.value

    def python_value(self, value) -> Enum:
        return self.enum_class(value)
