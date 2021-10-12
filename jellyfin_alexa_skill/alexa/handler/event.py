from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_request_type
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.util import set_shuffle_queue_idxs, build_audio_stream_response
from jellyfin_alexa_skill.database.db import get_playback
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient


class PlaybackStartedEventHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("AudioPlayer.PlaybackStarted")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        playback.playing = True
        playback.offset = 0
        playback.save()

        return handler_input.response_builder.response


class PlaybackFinishedEventHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("AudioPlayer.PlaybackFinished")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        playback.playing = False
        playback.offset = 0
        # increase counter if there are more items in the queue or loop all
        if playback.current_idx + 1 < len(playback.queue) or playback.loop_all:
            playback.current_idx = (playback.current_idx + 1) % len(playback.queue)
        playback.save()

        return handler_input.response_builder.response


class PlaybackStoppedEventHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("AudioPlayer.PlaybackStopped")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        playback.playing = False
        playback.save()

        return handler_input.response_builder.response


class PlaybackNearlyFinishedEventHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("AudioPlayer.PlaybackNearlyFinished")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        if playback.playing and (playback.current_idx + 1 < len(playback.queue)
                                 or playback.loop_all or playback.loop_single):
            if playback.loop_single:
                idx = playback.current_idx
            elif playback.shuffle:
                if not playback.shuffle_idxs:
                    # create a new shuffle idxs
                    set_shuffle_queue_idxs(playback)
                    playback.save()

                idx = playback.shuffle_idxs[playback.current_idx]
            else:
                idx = (playback.current_idx + 1) % len(playback.queue)

            build_audio_stream_response(self.jellyfin_client, handler_input, playback, idx)

        return handler_input.response_builder.response


class PlaybackFailedEventHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("AudioPlayer.PlaybackFailed")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        playback.playing = False
        playback.save()

        handler_input.response_builder.speak("Something went wrong during media playback. Please try again.")

        return handler_input.response_builder.response
