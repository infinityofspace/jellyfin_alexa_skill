import gettext

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.handler import BaseHandler
from jellyfin_alexa_skill.database.model.user import User


class CheckAudioInterfaceHandler(BaseHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        if handler_input.request_envelope.context.system.device:
            return handler_input.request_envelope.context.system.device.supported_interfaces.audio_player is None
        else:
            return False

    @BaseHandler.translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: gettext.GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        text = translation.gettext("Sorry, this device does not support media playback.")
        handler_input.response_builder.speak(text).set_should_end_session(True)
        return handler_input.response_builder.response
