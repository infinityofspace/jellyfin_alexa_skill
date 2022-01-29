import logging

from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

from jellyfin_alexa_skill.config import get_translation


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """
    Catch all exception handler, log exception and
    respond with error info message.
    """

    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True

    def handle(self,
               handler_input: HandlerInput,
               exception: Exception,
               *args, **kwargs) -> Response:
        translation = get_translation(handler_input.request_envelope.request.locale)

        logging.error(exception, exc_info=True)

        speech = translation.gettext("Sorry, something went wrong. Please try again.")
        handler_input.response_builder.speak(speech)

        return handler_input.response_builder.response
