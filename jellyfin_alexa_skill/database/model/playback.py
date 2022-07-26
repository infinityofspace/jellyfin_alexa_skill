import random
from typing import Optional, List

import peewee
from peewee import CharField, IntegerField, BooleanField, DeferredForeignKey, ForeignKeyField, TextField, AutoField

from jellyfin_alexa_skill.database.model.base import BaseModel, CharEnumField
from jellyfin_alexa_skill.jellyfin.api.client import MediaType

SHUFFLE_RANDOM_RANGE = (-424242, 424242)


class QueueItem(BaseModel):
    id = AutoField()
    playback = DeferredForeignKey("Playback", backref="items", on_delete="CASCADE", null=True)
    idx = IntegerField(null=False)
    media_type = CharEnumField(MediaType, null=False)
    item_id = TextField(null=False)

    class Meta:
        table_name = "QueueItem"


class Playback(BaseModel):
    user_id = CharField(primary_key=True)
    playing = BooleanField(default=False)
    current_item = ForeignKeyField(QueueItem, null=True)
    loop_single = BooleanField(default=False, null=False)
    loop_all = BooleanField(default=False, null=False)
    offset = IntegerField(default=0, null=False)
    shuffle = BooleanField(default=False, null=False)
    shuffle_random = IntegerField(null=True)
    shuffle_idx = IntegerField(null=True)

    class Meta:
        table_name = "Playback"

    def next(self) -> Optional[QueueItem]:
        """
        Sets the next item in the queue as the current item.

        :return: The next item in the queue or None if there is no next item.
        """

        if not self.current_item:
            return None

        if self.loop_single:
            return self.current_item

        if self.shuffle:
            if not self.shuffle_random:
                self.shuffle_random = random.randint(*SHUFFLE_RANDOM_RANGE)
            if not self.shuffle_idx:
                self.shuffle_idx = 0

            try:
                next_item = QueueItem.get(QueueItem.playback == self) \
                    .oder_by(self.shuffle_random) \
                    .skip(self.shuffle_idx) \
                    .first()

                if not next_item:
                    self.shuffle_idx = None
                else:
                    self.shuffle_idx += 1
            except peewee.DoesNotExist:
                self.shuffle_idx = None
                next_item = None
        else:
            try:
                next_item = QueueItem.get(QueueItem.playback == self, QueueItem.idx == self.current_item.idx + 1)
            except peewee.DoesNotExist:
                if self.loop_all:
                    try:
                        # try to go to the first item
                        next_item = QueueItem.get(QueueItem.playback == self, QueueItem.idx == 0)
                    except peewee.DoesNotExist:
                        next_item = None
                else:
                    next_item = None

        return next_item

    def previous(self) -> Optional[QueueItem]:
        """
        Sets the previous item in the queue as the current item.

        :return: The previous item in the queue or None if there is no previous item.
        """

        if not self.current_item:
            return None

        if self.loop_single:
            return self.current_item

        if self.shuffle:
            if not self.shuffle_random:
                self.shuffle_random = random.randint(*SHUFFLE_RANDOM_RANGE)
            if not self.shuffle_idx:
                self.shuffle_idx = 0

            try:
                prev_item = QueueItem.get(QueueItem.playback == self) \
                    .oder_by(self.shuffle_random) \
                    .skip(self.shuffle_idx - 1) \
                    .first()
                self.shuffle_idx -= 1

                if not prev_item:
                    self.shuffle_idx = None
                else:
                    self.shuffle_idx += 1
            except peewee.DoesNotExist:
                self.shuffle_idx = None
                prev_item = None
        else:
            try:
                prev_item = QueueItem.get(QueueItem.playback == self, QueueItem.idx == self.current_item.idx - 1)
            except peewee.DoesNotExist:
                if self.loop_all:
                    try:
                        # try to get the last item in the queue
                        prev_item = QueueItem.select(QueueItem.playback == self).order_by(QueueItem.idx.desc()).first()
                    except peewee.DoesNotExist:
                        prev_item = None
                else:
                    prev_item = None

        return prev_item

    def set_queue(self, items: List[QueueItem]) -> None:
        """
        Sets the queue to the given list of queue items and delete all old queue items in the database.
        Moreover, the offset is set to 0 and when the item list is not empty the current item is set to the first item
        of the list. Otherwise, the current item is set to None.
        """

        # first clear the old queue items
        QueueItem.delete().where(QueueItem.playback == self).execute()

        for item in items:
            item.playback = self
            item.save()

        if len(items) > 0:
            self.current_item = items[0]
        else:
            self.current_item = None
        self.playing = False
        self.offset = 0
        self.save()

    def clear_queue(self) -> None:
        """
        Clears the current queue by deleting all queue items in the database and set the current item to None. Moreover,
        the playstate is set to stopped and the offset to 0.
        """

        QueueItem.delete().where(QueueItem.playback == self).execute()

        self.playing = False
        self.current_item = None
        self.offset = 0
        self.save()
