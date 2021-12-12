import gettext

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.handler import BaseHandler
from jellyfin_alexa_skill.alexa.util import translate
from jellyfin_alexa_skill.database.model.user import User
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient


class StartRemoteControlHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("StartRemoteControl")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: gettext.GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        return handler_input.response_builder.response


class StopRemoteControlHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("StopRemoteControl")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: gettext.GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        return handler_input.response_builder.response
