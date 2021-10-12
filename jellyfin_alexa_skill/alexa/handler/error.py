import logging

from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """
    Catch all exception handler, log exception and
    respond with error info message.
    """

    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True

    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        logging.error(exception, exc_info=True)

        speech = "Sorry, something went wrong. Please try again."
        handler_input.response_builder.speak(speech)

        return handler_input.response_builder.response
