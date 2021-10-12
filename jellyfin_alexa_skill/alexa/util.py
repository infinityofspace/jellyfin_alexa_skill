from random import shuffle

from ask_sdk_model.interfaces.audioplayer import PlayDirective, PlayBehavior, AudioItem, Stream, AudioItemMetadata

from jellyfin_alexa_skill.database.model.playback import Playback
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient


def set_shuffle_queue_idxs(playback: Playback) -> None:
    playback.shuffle_idxs = list(range(len(playback.queue)))
    shuffle(playback.shuffle_idxs)
    idx = playback.shuffle_idxs.index(playback.current_idx)

    playback.shuffle_idxs.insert(playback.current_idx, playback.shuffle_idxs.pop(idx))


def build_audio_stream_response(jellyfin_client: JellyfinClient,
                                handler_input,
                                playback: Playback,
                                idx: int):
    if playback.shuffle:
        item = playback.queue[playback.shuffle_idxs[idx]]
    else:
        item = playback.queue[idx]

    stream_url = jellyfin_client.get_stream_url(item_id=item["id"])

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


def build_video_stream_response(jellyfin_client: JellyfinClient,
                                handler_input,
                                playback: Playback):
    pass
