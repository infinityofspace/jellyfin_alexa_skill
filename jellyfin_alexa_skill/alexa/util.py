import logging
from difflib import SequenceMatcher
from enum import Enum
from functools import wraps
from random import shuffle

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.interfaces.audioplayer import PlayDirective, PlayBehavior, AudioItem, Stream, AudioItemMetadata
from ask_sdk_model.interfaces.videoapp import LaunchDirective, VideoItem, Metadata

from ask_sdk_model.interfaces.display import Image, ImageInstance

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

    stream = jellyfin_client.get_stream_url(item_id=item["id"], user_id=jellyfin_user_id, token=jellyfin_token)
    stream_type = stream[0]
    stream_url = stream[1]

    if stream_type == "audio":
        art_image = None
        art_url = jellyfin_client.get_art_url(item_id=item["id"], token=jellyfin_token)
        if art_url:
            art_image = Image( sources=[ImageInstance(url=art_url)] )

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
                        subtitle=" ,".join(item["artists"]),
                        art=art_image
                    )
                )
            )
        )
    elif stream_type == "video":
        handler_input.response_builder.add_directive(
            LaunchDirective(
                video_item=VideoItem(
                    source=stream_url,
                    metadata=Metadata(
                        title=item["title"]
                    )
                )
            )
        )
    else:
        logging.warning("Unknown stream_type [%s]",stream_type)

def translate(func):
    @wraps(func)
    def wrapper(self, handler_input: HandlerInput, *args, **kwargs):
        translation = get_translation(handler_input.request_envelope.request.locale)

        return func(self, handler_input=handler_input, translation=translation, *args, **kwargs)

    return wrapper


def get_similarity(s1: str, s2: str) -> float:
    return SequenceMatcher(lambda x: x in " \t,.:-;/&_", s1.lower(), s2.lower()).ratio()

def best_matches_by_idx(match_scores, max_matches=3):
    """
        takes a list of "match_scores" (floats) and returns list of indexes into match_scores corresponding to
        the top "max_matches" scores

        returns * list of 0-based indexes into match_scores corresponding to the top "max_matches"
                  note: the len() of the returned list will be the minimum of len(match_scores) and max_matches
                * an empty list if "match_scores" is empty

        example:  match_scores = [ 0.31, 0.4, 0.21, 0.8 ]  max_matches=3
                    ==> [ 3, 1, 0 ]  corresponding to match_scores[3], match_scores[1] and match_scores[0]
    """

    # the simple cases first
    if len(match_scores) == 0:
        return []
    if len(match_scores) == 1:
        return [ 0 ]

    # more complex cases: match_scores consists of 2 or more scores
    # step 1 - build a dictionary to remember the original index of each score in "match_scores"
    idx = 0
    indexed_scores = {}
    for score in match_scores:
        indexed_scores[idx] = score
        idx += 1

    # step 2 - sort the scores (by value) in descending order
    sorted_scores = {key: val for key, val in sorted(indexed_scores.items(), key = lambda item: item[1], reverse = True)}

    # step 3 - put the top "max_matches" indexes (by key) in a list
    idx = 0
    indexed_list = []
    for key in sorted_scores.keys():
        indexed_list.append(key)
        idx += 1
        if (idx >= max_matches):
           break

    return indexed_list
