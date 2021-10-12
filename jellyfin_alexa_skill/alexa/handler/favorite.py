from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.util import build_audio_stream_response
from jellyfin_alexa_skill.database.db import get_playback, set_playback_queue
from jellyfin_alexa_skill.database.model.playback import PlaybackItem
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient, MediaType


class PlayFavoritesIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayFavoritesIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        favorites = self.jellyfin_client.get_favorites()

        if favorites:
            playback_items = [PlaybackItem(item["Id"], item["Name"], item["Artists"])
                              for item in favorites]

            user_id = handler_input.request_envelope.session.user.user_id
            playback = set_playback_queue(user_id, playback_items)

            build_audio_stream_response(self.jellyfin_client, handler_input, playback, playback.current_idx)
        else:
            text = "Sorry, you don't have any favorite media."
            handler_input.response_builder.speak(text)

        return handler_input.response_builder.response


class PlayFavoriteSongsIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayFavoriteSongsIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        favorites = self.jellyfin_client.get_favorites(media_type=MediaType.AUDIO)

        if favorites:
            playback_items = [PlaybackItem(item["Id"], item["Name"], item["Artists"])
                              for item in favorites]

            user_id = handler_input.request_envelope.session.user.user_id
            playback = set_playback_queue(user_id, playback_items)

            build_audio_stream_response(self.jellyfin_client, handler_input, playback, playback.current_idx)
        else:
            text = "Sorry, you don't have any favorite songs."
            handler_input.response_builder.speak(text)

        return handler_input.response_builder.response


class PlayFavoriteVideosIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayFavoriteVideosIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        favorites = self.jellyfin_client.get_favorites(media_type=MediaType.VIDEO)

        if favorites:
            playback_items = [PlaybackItem(item["Id"], item["Name"], item["Artists"])
                              for item in favorites]

            user_id = handler_input.request_envelope.session.user.user_id
            playback = set_playback_queue(user_id, playback_items)

            build_audio_stream_response(self.jellyfin_client, handler_input, playback, playback.current_idx)
        else:
            text = "Sorry, you don't have any favorite videos."
            handler_input.response_builder.speak(text)

        return handler_input.response_builder.response


class MarkFavoriteIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("MarkFavoriteIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.session.user.user_id
        playback = get_playback(user_id)

        if playback.playing and playback.current_idx is not None:
            current_media_id = playback.queue[playback.current_idx]
            self.jellyfin_client.jellyfin.favorite(current_media_id, option=True)

            handler_input.response_builder.speak("Added to your favorites.")
        else:
            handler_input.response_builder.speak("There is currently no media playing.")

        return handler_input.response_builder.response


class UnmarkFavoriteIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("UnmarkFavoriteIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.session.user.user_id
        playback = get_playback(user_id)

        if playback.playing and playback.current_idx is not None:
            current_media_id = playback.queue[playback.current_idx]
            self.jellyfin_client.jellyfin.favorite(current_media_id, option=False)

            handler_input.response_builder.speak("Removed from your favorites.")
        else:
            handler_input.response_builder.speak("There is currently no media playing.")

        return handler_input.response_builder.response
