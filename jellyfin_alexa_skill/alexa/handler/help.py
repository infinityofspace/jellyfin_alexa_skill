from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        speech_text = "With this skill your can play media from your Jellyfin Server." \
                      "Use 'Play Game of Live from Earth' or 'Play playlist this is number 42' to play some songs."

        handler_input.response_builder.speak(speech_text)
        return handler_input.response_builder.response
