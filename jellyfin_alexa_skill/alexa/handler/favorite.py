from gettext import GNUTranslations

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.handler import BaseHandler
from jellyfin_alexa_skill.alexa.util import build_stream_response, MediaTypeSlot, translate
from jellyfin_alexa_skill.database.db import get_playback, set_playback_queue
from jellyfin_alexa_skill.database.model.playback import PlaybackItem
from jellyfin_alexa_skill.database.model.user import User
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient, MediaType


class PlayFavoritesIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayFavoritesIntent")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        media_type = handler_input.request_envelope.request.intent.slots["media_type"] \
            .resolutions.resolutions_per_authority[0].values[0].value.id

        if media_type == MediaTypeSlot.AUDIO:
            filter_media_type = MediaType.AUDIO
        elif media_type == MediaTypeSlot.VIDEO:
            filter_media_type = MediaType.VIDEO
        else:
            filter_media_type = None

        favorites = self.jellyfin_client.get_favorites(user_id=user.jellyfin_user_id,
                                                       token=user.jellyfin_token,
                                                       media_type=filter_media_type)

        if favorites:
            playback_items = [PlaybackItem(item["Id"], item["Name"], item["Artists"])
                              for item in favorites]

            user_id = handler_input.request_envelope.session.user.user_id
            playback = set_playback_queue(user_id, playback_items)

            build_stream_response(jellyfin_client=self.jellyfin_client,
                                  jellyfin_user_id=user.jellyfin_user_id,
                                  jellyfin_token=user.jellyfin_token,
                                  handler_input=handler_input,
                                  playback=playback,
                                  idx=playback.current_idx)
        else:
            text = translation.gettext("Sorry, you don't have any favorite media.")
            handler_input.response_builder.speak(text)

        return handler_input.response_builder.response


class MarkFavoriteIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("MarkFavoriteIntent")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        user_id = handler_input.request_envelope.session.user.user_id
        playback = get_playback(user_id)

        if playback.playing and playback.current_idx is not None:
            current_media_id = playback.queue[playback.current_idx]
            self.jellyfin_client.favorite(user_id=user.jellyfin_user_id,
                                          token=user.jellyfin_token,
                                          media_id=current_media_id)

            handler_input.response_builder.speak(translation.gettext("Added to your favorites."))
        else:
            handler_input.response_builder.speak(translation.gettext("There is currently no media playing."))

        return handler_input.response_builder.response


class UnmarkFavoriteIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("UnmarkFavoriteIntent")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        user_id = handler_input.request_envelope.session.user.user_id
        playback = get_playback(user_id)

        if playback.playing and playback.current_idx is not None:
            current_media_id = playback.queue[playback.current_idx]
            self.jellyfin_client.unfavorite(user_id=user.jellyfin_user_id,
                                            token=user.jellyfin_token,
                                            media_id=current_media_id)

            handler_input.response_builder.speak(translation.gettext("Removed from your favorites."))
        else:
            handler_input.response_builder.speak(translation.gettext("There is currently no media playing."))

        return handler_input.response_builder.response
