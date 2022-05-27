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


def clear_db() -> None:
    db.drop_tables([User, Playback, QueueItem], safe=True)
    db.create_tables([User, Playback, QueueItem], safe=True)


def get_playback(user_id: str) -> Playback:
    return Playback.get_or_create(user_id=user_id)[0]
