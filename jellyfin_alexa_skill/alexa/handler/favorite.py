from gettext import GNUTranslations

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.handler import BaseHandler
from jellyfin_alexa_skill.alexa.util import build_stream_response, get_media_type_enum, AlexaMediaType
from jellyfin_alexa_skill.database.db import get_playback
from jellyfin_alexa_skill.database.model.playback import QueueItem
from jellyfin_alexa_skill.database.model.user import User
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient, MediaType


class PlayFavoritesIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayFavoritesIntent")(handler_input)

    @BaseHandler.translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        media_type_resolutions = handler_input.request_envelope.request.intent.slots["media_type"].resolutions

        if media_type_resolutions is None:
            filter_media_type = None
        else:
            media_type = media_type_resolutions.resolutions_per_authority[0].values[0].value.id

            if media_type == AlexaMediaType.AUDIO.value:
                filter_media_type = MediaType.AUDIO
            elif media_type == AlexaMediaType.VIDEO.value:
                filter_media_type = MediaType.VIDEO
            else:
                filter_media_type = None

        favorites = self.jellyfin_client.get_favorites(user_id=user.jellyfin_user_id,
                                                       token=user.jellyfin_token,
                                                       media_type=filter_media_type)

        if favorites:
            user_id = handler_input.request_envelope.session.user.user_id
            queue_items = [QueueItem(idx=i,
                                     media_type=get_media_type_enum(item_info),
                                     media_item_id=item_info["Id"]) for i, item_info in enumerate(favorites)]

            playback = get_playback(user_id)
            playback.set_queue(queue_items)

            build_stream_response(jellyfin_client=self.jellyfin_client,
                                  jellyfin_user_id=user.jellyfin_user_id,
                                  jellyfin_token=user.jellyfin_token,
                                  handler_input=handler_input,
                                  queue_item=playback.current_item)
        else:
            text = translation.gettext("Sorry, you don't have any favorite media.")
            handler_input.response_builder.speak(text)

        return handler_input.response_builder.response


class MarkFavoriteIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("MarkFavoriteIntent")(handler_input)

    @BaseHandler.translate
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

    @BaseHandler.translate
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
