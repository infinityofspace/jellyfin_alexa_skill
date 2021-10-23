import logging
from gettext import GNUTranslations

from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.util import translate


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """
    Catch all exception handler, log exception and
    respond with error info message.
    """

    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True

    @translate
    def handle(self,
               handler_input: HandlerInput,
               exception: Exception,
               translation: GNUTranslations,
               *args, **kwargs) -> Response:
        logging.error(exception, exc_info=True)

        speech = translation.gettext("Sorry, something went wrong. Please try again.")
        handler_input.response_builder.speak(speech)

        return handler_input.response_builder.response
