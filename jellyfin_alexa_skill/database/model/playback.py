import json
from typing import List

from peewee import CharField, IntegerField, BooleanField
from playhouse.sqlite_ext import JSONField

from jellyfin_alexa_skill.database.model.base import BaseModel


class PlaybackItem(dict):
    def __init__(self, id: str, title: str, artists: List[str]):
        super().__init__(id=id, title=title, artists=artists)


def json_dumps(value):
    return json.dumps(value)


def json_loads(value):
    return json.loads(value)


class Playback(BaseModel):
    user_id = CharField(primary_key=True)
    playing = BooleanField(default=False)
    current_idx = IntegerField(default=0)
    queue = JSONField(default=[], json_dumps=json_dumps, json_loads=json_loads)
    loop_single = BooleanField(default=False)
    loop_all = BooleanField(default=False)
    offset = IntegerField(default=0)
    shuffle = BooleanField(default=False)
    shuffle_idxs = JSONField(default=[])

    class Meta:
        table_name = "Playback"
