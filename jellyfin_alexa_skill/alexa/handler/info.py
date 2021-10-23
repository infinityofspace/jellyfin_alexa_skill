from gettext import GNUTranslations

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.handler.base import BaseHandler
from jellyfin_alexa_skill.alexa.util import translate
from jellyfin_alexa_skill.database.db import get_current_played_item
from jellyfin_alexa_skill.database.model.user import User


class MediaInfoIntentHandler(BaseHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("MediaInfoIntent")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id
        item = get_current_played_item(user_id)

        if item:
            speech_text = translation.gettext("Currently playing {title} from {artists}.".format(title=item["title"],
                                                                                                artists=" ,".join(
                                                                                                    item["artists"])))
        else:
            speech_text = translation.gettext("Currently no media is played.")

        handler_input.response_builder.speak(speech_text)
        return handler_input.response_builder.response
