from difflib import SequenceMatcher
from enum import Enum

from ask_sdk_model.interfaces.audioplayer import PlayDirective, PlayBehavior, AudioItem, Stream, AudioItemMetadata
from ask_sdk_model.interfaces.display import Image, ImageInstance
from ask_sdk_model.interfaces.videoapp import LaunchDirective, VideoItem, Metadata

from jellyfin_alexa_skill.database.model.playback import QueueItem
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient, MediaType


class AlexaMediaType(Enum):
    AUDIO = "audio"
    VIDEO = "video"


def build_stream_response(jellyfin_client: JellyfinClient,
                          jellyfin_user_id: str,
                          jellyfin_token: str,
                          handler_input,
                          queue_item: QueueItem,
                          offset: int = 0) -> None:
    url, play_info = jellyfin_client.get_stream_url(item_id=queue_item.item_id,
                                                    user_id=jellyfin_user_id,
                                                    token=jellyfin_token)

    if queue_item.media_type == MediaType.AUDIO:
        primary_image_url = jellyfin_client.server_endpoint + f"/Items/{queue_item.item_id}/Images/Primary"
        art_image = Image(sources=[ImageInstance(url=primary_image_url)])

        handler_input.response_builder.add_directive(
            PlayDirective(
                play_behavior=PlayBehavior.REPLACE_ALL,
                audio_item=AudioItem(
                    stream=Stream(
                        token=queue_item.item_id,
                        url=url,
                        offset_in_milliseconds=offset),
                    metadata=AudioItemMetadata(
                        title=play_info.get("name", "Unknown Title"),
                        subtitle=" ,".join(play_info.get("artists", [])),
                        art=art_image
                    )
                )
            )
        )
    else:
        # confirm that device supports video
        if not handler_input.request_envelope.context.system.device.supported_interfaces.video_app:
            handler_input.response_builder.speak("Sorry, this device does not support video playback.")
            return

        handler_input.response_builder.add_directive(
            LaunchDirective(
                video_item=VideoItem(
                    source=url,
                    metadata=Metadata(
                        title=play_info.get("name", "Unknown Title")
                    )
                )
            )
        )


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
        return [0]

    # more complex cases: match_scores consists of 2 or more scores
    # step 1 - build a dictionary to remember the original index of each score in "match_scores"
    idx = 0
    indexed_scores = {}
    for score in match_scores:
        indexed_scores[idx] = score
        idx += 1

    # step 2 - sort the scores (by value) in descending order
    sorted_scores = {key: val for key, val in sorted(indexed_scores.items(), key=lambda item: item[1], reverse=True)}

    # step 3 - put the top "max_matches" indexes (by key) in a list
    idx = 0
    indexed_list = []
    for key in sorted_scores.keys():
        indexed_list.append(key)
        idx += 1
        if idx >= max_matches:
            break

    return indexed_list


def get_media_type_enum(item_info: dict) -> MediaType:
    if item_info["MediaType"] == "Audio":
        return MediaType.AUDIO
    elif item_info["MediaType"] == "Video":
        return MediaType.VIDEO
    elif item_info["MediaType"] == "LiveTv":
        return MediaType.CHANNEL
    else:
        raise ValueError(f"Unknown media type: {item_info['MediaType']}")
