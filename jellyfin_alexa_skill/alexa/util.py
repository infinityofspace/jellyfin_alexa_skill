from difflib import SequenceMatcher
from enum import Enum
from functools import wraps
from random import shuffle

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.interfaces.audioplayer import PlayDirective, PlayBehavior, AudioItem, Stream, AudioItemMetadata

from jellyfin_alexa_skill.config import get_translation
from jellyfin_alexa_skill.database.model.playback import Playback
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient


class MediaTypeSlot(Enum):
    MEDIA = "media"
    VIDEO = "video"
    AUDIO = "audio"


def set_shuffle_queue_idxs(playback: Playback) -> None:
    playback.shuffle_idxs = list(range(len(playback.queue)))
    shuffle(playback.shuffle_idxs)
    idx = playback.shuffle_idxs.index(playback.current_idx)

    playback.shuffle_idxs.insert(playback.current_idx, playback.shuffle_idxs.pop(idx))


def build_stream_response(jellyfin_client: JellyfinClient,
                          jellyfin_user_id: str,
                          jellyfin_token: str,
                          handler_input,
                          playback: Playback,
                          idx: int):
    if playback.shuffle:
        item = playback.queue[playback.shuffle_idxs[idx]]
    else:
        item = playback.queue[idx]

    stream_url = jellyfin_client.get_stream_url(item_id=item["id"], user_id=jellyfin_user_id, token=jellyfin_token)

    handler_input.response_builder.add_directive(
        PlayDirective(
            play_behavior=PlayBehavior.REPLACE_ALL,
            audio_item=AudioItem(
                stream=Stream(
                    token=item["id"],
                    url=stream_url,
                    offset_in_milliseconds=0),
                metadata=AudioItemMetadata(
                    title=item["title"],
                    subtitle=" ,".join(item["artists"])
                )
            )
        )
    )


def translate(func):
    @wraps(func)
    def wrapper(self, handler_input: HandlerInput, *args, **kwargs):
        translation = get_translation(handler_input.request_envelope.request.locale)

        return func(self, handler_input=handler_input, translation=translation, *args, **kwargs)

    return wrapper


def get_similarity(s1: str, s2: str) -> float:
    return SequenceMatcher(lambda x: x in " \t,.:-;/", s1.lower(), s2.lower()).ratio()
