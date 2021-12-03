from gettext import GNUTranslations

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response
from jellyfin_alexa_skill.alexa.handler.base import BaseHandler
from jellyfin_alexa_skill.alexa.util import translate, build_stream_response
from jellyfin_alexa_skill.database.db import set_playback_queue
from jellyfin_alexa_skill.database.model.playback import PlaybackItem
from jellyfin_alexa_skill.database.model.user import User
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient


class YesNoIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    """
       Handler for Yes/No dialog with user
    """
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ( is_intent_name("AMAZON.YesIntent")(handler_input) \
                 or is_intent_name("AMAZON.NoIntent")(handler_input) )

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:

        # if we don't have TopMatches attributes, just return
        if "TopMatches" not in handler_input.attributes_manager.session_attributes:
            return handler_input.response_builder.response

        if len(handler_input.attributes_manager.session_attributes["TopMatches"]) == 0:
            return handler_input.response_builder.response

        # handle the yes/no response
        if handler_input.request_envelope.request.intent.name == "AMAZON.YesIntent":
            # user wants to play the top match

            # grab the top match, then cleanup the TopMatches list
            item = handler_input.attributes_manager.session_attributes["TopMatches"][0]
            handler_input.attributes_manager.session_attributes["TopMatches"].clear()

            user_id = handler_input.request_envelope.context.system.user.user_id
            playback = set_playback_queue(user_id, [PlaybackItem(item["Id"], item["Name"], item["Artist"])])

            build_stream_response(jellyfin_client=self.jellyfin_client,
                                  jellyfin_user_id=user.jellyfin_user_id,
                                  jellyfin_token=user.jellyfin_token,
                                  handler_input=handler_input,
                                  playback=playback,
                                  idx=0)

            return handler_input.response_builder.response

        # AMAZON.NoIntent - remove the top match, and ask user if they want the next match

        handler_input.attributes_manager.session_attributes["TopMatches"].pop(0)

        if handler_input.attributes_manager.session_attributes["TopMatches"]:
            item = handler_input.attributes_manager.session_attributes["TopMatches"][0]

            artists = item["Artist"]
            by_artist = ""
            if len(artists) > 0:
                by_artist = translation.gettext("by {artist}".format(artist=artists[0]))

            request_text = translation.gettext("Hmm. How about <break/> {title} {by_artist} ?".format(
                                                                                     title=item['Name'],
                                                                                     by_artist=by_artist))

            return handler_input.response_builder.speak(request_text).ask(request_text).response
        else:
            speak_output = translation.gettext("I'm all out of guesses.  Please try asking a different way.")
            handler_input.response_builder.speak(speak_output)
            return handler_input.response_builder.response
