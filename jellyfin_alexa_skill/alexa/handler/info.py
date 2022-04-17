from gettext import GNUTranslations

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response

from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient
from jellyfin_alexa_skill.alexa.handler.base import BaseHandler
from jellyfin_alexa_skill.database.db import get_playback
from jellyfin_alexa_skill.database.model.user import User


class MediaInfoIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("MediaInfoIntent")(handler_input)

    @BaseHandler.translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id
        playback = get_playback(user_id)

        if playback.current_item:
            item_info = self.jellyfin_client.get_item_info(user_id=user.jellyfin_user_id,
                                                           token=user.jellyfin_token,
                                                           media_id=playback.current_item.item_id)
            title = item_info.get("Name", translation.gettext("Unknown title"))
            artists = item_info.get("Artists", [])
            if not artists:
                artists_str = translation.gettext("Unknown artist")
            else:
                artists_str = ", ".join(artists)
            speech_text = translation.gettext("Currently playing {title} from {artists}.".format(title=title,
                                                                                                 artists=artists_str))
        else:
            speech_text = translation.gettext("Currently no media is played.")

        handler_input.response_builder.speak(speech_text)
        return handler_input.response_builder.response
