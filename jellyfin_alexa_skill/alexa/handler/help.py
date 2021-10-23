from gettext import GNUTranslations

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.handler.base import BaseHandler
from jellyfin_alexa_skill.alexa.util import translate
from jellyfin_alexa_skill.database.model.user import User


class HelpIntentHandler(BaseHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        speech_text = translation.gettext("With this skill your can play media from your Jellyfin Server. "
                                          "Use 'Play Game of Live from Earth' or 'Play playlist this is number 42' to play some songs.")

        handler_input.response_builder.speak(speech_text)
        return handler_input.response_builder.response
