from gettext import GNUTranslations

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.handler import BaseHandler
from jellyfin_alexa_skill.alexa.util import build_stream_response, MediaTypeSlot
from jellyfin_alexa_skill.database.db import get_playback, set_playback_queue
from jellyfin_alexa_skill.database.model.playback import PlaybackItem
from jellyfin_alexa_skill.database.model.user import User
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient, MediaType


class ShuffleIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("ShuffleIntent")(handler_input)

    @BaseHandler.translate
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

        shuffle = self.jellyfin_client.get_shuffle(user_id=user.jellyfin_user_id,
                                                       token=user.jellyfin_token,
                                                       media_type=filter_media_type)
        if shuffle:
            playback_items = [PlaybackItem(item.get("Id"), item.get("Name"), item.get("Artists"))
                              for item in shuffle]

            user_id = handler_input.request_envelope.session.user.user_id
            playback = set_playback_queue(user_id, playback_items)

            build_stream_response(jellyfin_client=self.jellyfin_client,
                                  jellyfin_user_id=user.jellyfin_user_id,
                                  jellyfin_token=user.jellyfin_token,
                                  handler_input=handler_input,
                                  playback=playback,
                                  idx=playback.current_idx)
        else:
            text = translation.gettext("Sorry, I can't find any songs for this search. Please try again.")
            handler_input.response_builder.speak(text)

        return handler_input.response_builder.response