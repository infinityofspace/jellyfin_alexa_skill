import itertools
import unittest

from database.model.playback import Playback, QueueItem
from jellyfin.api.client import MediaType
from jellyfin_alexa_skill.database.db import connect_db, close_db, get_playback, clear_playback_queue, \
    set_playback_queue
from jellyfin_alexa_skill.database.model.base import db

USER_ID = "123456id"


class TestDB(unittest.TestCase):
    def test_db_connection(self):
        db_path = ":memory:"
        connect_db(db_path)

        self.assertFalse(db.is_closed())

        close_db()

        self.assertTrue(db.is_closed())


class TestPlaybackModel(unittest.TestCase):
    def setUp(self) -> None:
        db_path = ":memory:"
        connect_db(db_path)

        self.playback = Playback.create(user_id=USER_ID)
        self.playback.save()
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
    def test_get_playback(self):
        db_path = ":memory:"
        connect_db(db_path)

        playback = Playback.create(user_id=USER_ID)
        playback.save()
        items = [QueueItem.create(playback=playback, idx=i, media_type=MediaType.AUDIO, item_id=f"abc{i}")
                 for i in range(10)]

        playback = get_playback(USER_ID)
        self.assertEqual(playback.user_id, playback.user_id)

        db.close()

    def test_clear_playback(self):
        db_path = ":memory:"
        connect_db(db_path)

        playback = Playback.create(user_id=USER_ID)
        playback.save()
        items = [QueueItem.create(playback=playback, idx=i, media_type=MediaType.AUDIO, item_id=f"abc{i}")
                 for i in range(10)]

        clear_playback_queue(USER_ID)

        items = list(QueueItem.select(QueueItem.playback == playback))
        self.assertEqual(items, [])

        db.close()

    def test_set_playback_queue(self):
        db_path = ":memory:"
        connect_db(db_path)

        playback = Playback.create(user_id=USER_ID)
        playback.save()
        items = [QueueItem(idx=i, media_type=MediaType.AUDIO, item_id=f"abc{i}")
                 for i in range(10)]

        playback = set_playback_queue(USER_ID, items)

        self.assertEqual(playback.current_item.id, items[0].id)
        self.assertEqual(playback.offset, 0)
        self.assertEqual(playback.playing, False)

        db.close()

    def test_set_playback_queue_empty(self):
        db_path = ":memory:"
        connect_db(db_path)

        playback = Playback.create(user_id=USER_ID)
        playback.save()
        items = [QueueItem.create(playback=playback, idx=i, media_type=MediaType.AUDIO, item_id=f"abc{i}")
                 for i in range(10)]

        playback = set_playback_queue(USER_ID, [])

        self.assertEqual(playback.current_item, None)
        self.assertEqual(playback.offset, 0)
        self.assertEqual(playback.playing, False)
        # there should be no items in the queue
        self.assertEqual(QueueItem.select().where(QueueItem.playback == playback).count(), 0)

        db.close()


if __name__ == "__main__":
    unittest.main()
