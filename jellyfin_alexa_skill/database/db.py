from typing import List

from peewee import Database
from playhouse.pool import PooledPostgresqlDatabase

from jellyfin_alexa_skill.database.model.base import db
from jellyfin_alexa_skill.database.model.playback import Playback, QueueItem
from jellyfin_alexa_skill.database.model.user import User


def connect_db(user: str,
               password: str,
               host: str,
               port: int = 5432,
               database: str = "jellyfin_alexa_skill") -> Database:
    db.initialize(PooledPostgresqlDatabase(database=database,
                                           user=user,
                                           password=password,
                                           host=host,
                                           port=port,
                                           max_connections=8,
                                           stale_timeout=300))

    db.connect(reuse_if_open=True)

    db.create_tables([User, Playback, QueueItem], safe=True)

    return db


def close_db() -> None:
    db.close()


def get_playback(user_id: str) -> Playback:
    return Playback.get_or_create(user_id=user_id)[0]


def clear_playback_queue(user_id: str) -> None:
    playback = get_playback(user_id)
    QueueItem.delete().where(QueueItem.playback == playback).execute()

    playback.playing = False
    playback.current_item = None
    playback.offset = 0
    playback.save()


def set_playback_queue(user_id: str, items: List[QueueItem]) -> Playback:
    playback = get_playback(user_id)
    # first clear the old queue items
    QueueItem.delete().where(QueueItem.playback == playback).execute()

    for item in items:
        item.playback = playback
        item.save()

    if len(items) > 0:
        playback.current_item = QueueItem.get(id=items[0].id)
    else:
        playback.current_item = None
    playback.playing = False
    playback.offset = 0
    playback.save()

    return playback
