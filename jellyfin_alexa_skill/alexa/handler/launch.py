from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_request_type
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.util import build_audio_stream_response
from jellyfin_alexa_skill.database.db import get_playback
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient


class LaunchRequestHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id
        playback = get_playback(user_id)

        if playback.queue:
            build_audio_stream_response(self.jellyfin_client, handler_input, playback, playback.current_idx)
        else:
            speech_text = "Welcome to Jellyfin Player skill, what can I play?"

            handler_input.response_builder.speak(speech_text).set_should_end_session(False)

        return handler_input.response_builder.response


class CheckAudioInterfaceHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        if handler_input.request_envelope.context.system.device:
            return handler_input.request_envelope.context.system.device.supported_interfaces.audio_player is None
        else:
            return False

    def handle(self, handler_input: HandlerInput) -> Response:
        text = "Sorry, this device does not support media playback."
        handler_input.response_builder.speak(text).set_should_end_session(True)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.response
