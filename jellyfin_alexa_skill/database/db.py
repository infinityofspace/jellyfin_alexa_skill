from pathlib import Path
from typing import Union, List

from jellyfin_alexa_skill.database.model.base import db
from jellyfin_alexa_skill.database.model.playback import Playback, QueueItem
from jellyfin_alexa_skill.database.model.user import User


def connect_db(path: Union[Path, str]) -> None:
    db.init(str(path))
    db.connect()

    db.create_tables([User, Playback, QueueItem], safe=True)


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
