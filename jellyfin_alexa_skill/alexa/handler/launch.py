import gettext

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_request_type
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.handler import BaseHandler
from jellyfin_alexa_skill.alexa.util import build_stream_response
from jellyfin_alexa_skill.database.db import get_playback
from jellyfin_alexa_skill.database.model.user import User
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient


class LaunchRequestHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("LaunchRequest")(handler_input)

    @BaseHandler.translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: gettext.GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id
        playback = get_playback(user_id)

        if playback.queue:
            build_stream_response(jellyfin_client=self.jellyfin_client,
                                  jellyfin_user_id=user.jellyfin_user_id,
                                  jellyfin_token=user.jellyfin_token,
                                  handler_input=handler_input,
                                  playback=playback,
                                  idx=playback.current_idx)
        else:
            speech_text = translation.gettext("Welcome to Jellyfin Player skill, what can I play?")

            handler_input.response_builder.speak(speech_text).set_should_end_session(False)

        return handler_input.response_builder.response
