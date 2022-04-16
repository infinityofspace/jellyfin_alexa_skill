import random
from typing import Optional

import peewee
from peewee import CharField, IntegerField, BooleanField, DeferredForeignKey, ForeignKeyField

from jellyfin.api.client import MediaType
from jellyfin_alexa_skill.database.model.base import BaseModel, CharEnumField

SHUFFLE_RANDOM_RANGE = (-424242, 424242)


class QueueItem(BaseModel):
    id = IntegerField(primary_key=True)
    playback = DeferredForeignKey("Playback", backref="items")
    idx = IntegerField(null=False)
    media_type = CharEnumField(MediaType, null=False)
    item_id = CharField(null=False)

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
