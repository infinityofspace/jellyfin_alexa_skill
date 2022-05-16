import itertools
import unittest

from peewee import SqliteDatabase

from jellyfin_alexa_skill.database.db import close_db, get_playback, clear_playback_queue, \
    set_playback_queue
from jellyfin_alexa_skill.database.model.base import db
from jellyfin_alexa_skill.database.model.playback import Playback, QueueItem
from jellyfin_alexa_skill.database.model.user import User
from jellyfin_alexa_skill.jellyfin.api.client import MediaType

USER_ID = "123456id"


def connect_db():
    db.initialize(SqliteDatabase(":memory:"))

    db.connect(reuse_if_open=True)

    db.create_tables([User, Playback, QueueItem], safe=True)


class TestDB(unittest.TestCase):
    def test_db_connection(self):
        connect_db()

        self.assertFalse(db.is_closed())

        close_db()

        self.assertTrue(db.is_closed())


class TestPlaybackModel(unittest.TestCase):
    def setUp(self) -> None:
        connect_db()

        self.playback = Playback.create(user_id=USER_ID)
        self.items = [QueueItem.create(playback=self.playback, idx=i, media_type=MediaType.AUDIO, item_id=f"abc{i}")
                      for i in range(10)]

    def tearDown(self) -> None:
        db.close()

    def test_next(self):
        # the first item should be None
        next_item = self.playback.next()
        self.assertIsNone(next_item)

        # now we enable the playback with the first item
        self.playback.current_item = self.items[0]
        self.playback.save()

        for item in self.items[1:]:
            next_item = self.playback.next()
            self.assertEqual(next_item, item)
            self.playback.current_item = next_item

        # the next item should be None
        next_item = self.playback.next()
        self.assertIsNone(next_item)

        # the next item should also be None
        next_item = self.playback.next()
        self.assertIsNone(next_item)

    def test_next_empty(self):
        clear_playback_queue(USER_ID)
        # the first item should be None
        next_item = self.playback.next()
        self.assertIsNone(next_item)

    def test_next_loop_single(self):
        self.playback.loop_single = True
        self.playback.save()

        # the first item should be None
        next_item = self.playback.next()
        self.assertIsNone(next_item)

        # now we enable the playback with the first item
        self.playback.current_item = self.items[0]
        self.playback.save()

        next_item = self.playback.next()
        self.assertEqual(next_item, self.items[0])
        next_item = self.playback.next()
        self.assertEqual(next_item, self.items[0])

    def test_next_loop_all(self):
        self.playback.loop_all = True
        self.playback.save()

        # the first item should be None
        next_item = self.playback.next()
        self.assertIsNone(next_item)

        # now we enable the playback with the first item
        self.playback.current_item = self.items[0]
        self.playback.save()

        for item in self.items[1:]:
            next_item = self.playback.next()
            self.assertEqual(next_item, item)
            self.playback.current_item = next_item

        for i, item in enumerate(itertools.cycle(self.items)):
            next_item = self.playback.next()
            self.assertEqual(next_item, item)
            self.playback.current_item = next_item
            if i > len(self.items) * 5:
                break

    def test_previous(self):
        # the previous item should be now None
        prev_item = self.playback.previous()
        self.assertIsNone(prev_item)

        # now we enable the playback with the last item
        self.playback.current_item = self.items[-1]
        self.playback.save()

        for item in reversed(self.items[:-1]):
            prev_item = self.playback.previous()
            self.assertEqual(prev_item, item)

            self.playback.current_item = prev_item

        # the previous item should be now None
        prev_item = self.playback.previous()
        self.assertIsNone(prev_item)


class TestDBMethods(unittest.TestCase):
    def setUp(self) -> None:
        connect_db()

        self.playback = Playback.create(user_id=USER_ID)
        self.items = [QueueItem.create(playback=self.playback, idx=i, media_type=MediaType.AUDIO, item_id=f"abc{i}")
                      for i in range(10)]

    def tearDown(self) -> None:
        db.close()

    def test_get_playback(self):
        playback = get_playback(USER_ID)
        self.assertEqual(playback.user_id, playback.user_id)

    def test_clear_playback(self):
        clear_playback_queue(USER_ID)

        items = list(QueueItem.select(QueueItem.playback == self.playback))
        self.assertEqual(items, [])

    def test_set_playback_queue(self):
        get_playback(USER_ID)
        items = [QueueItem(idx=i, media_type=MediaType.AUDIO, item_id=f"abc{i}")
                 for i in range(10)]

        playback = set_playback_queue(USER_ID, items)

        self.assertEqual(playback.current_item.id, items[0].id)
        self.assertEqual(playback.offset, 0)
        self.assertEqual(playback.playing, False)

    def test_set_playback_queue_empty(self):
        playback = set_playback_queue(USER_ID, [])

        self.assertEqual(playback.current_item, None)
        self.assertEqual(playback.offset, 0)
        self.assertEqual(playback.playing, False)
        # there should be no items in the queue
        self.assertEqual(QueueItem.select().where(QueueItem.playback == playback).count(), 0)


if __name__ == "__main__":
    unittest.main()
