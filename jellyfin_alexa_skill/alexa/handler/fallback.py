from gettext import GNUTranslations

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.util import translate


class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    @translate
    def handle(self,
               handler_input: HandlerInput,
               translation: GNUTranslations,
               *args,
               **kwargs) -> Response:
        handler_input.response_builder.speak(
            translation.gettext("Sorry, I could not understand that. Please try again."))

        return handler_input.response_builder.response
