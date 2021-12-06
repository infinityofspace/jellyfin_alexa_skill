from gettext import GNUTranslations

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.handler.base import BaseHandler
from jellyfin_alexa_skill.alexa.util import build_stream_response, MediaTypeSlot, translate, get_similarity, best_matches_by_idx
from jellyfin_alexa_skill.database.db import set_playback_queue
from jellyfin_alexa_skill.database.model.playback import PlaybackItem
from jellyfin_alexa_skill.database.model.user import User
from jellyfin_alexa_skill.jellyfin.api.client import MediaType, JellyfinClient


class PlayChannelIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayChannelIntent")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        channel = handler_input.request_envelope.request.intent.slots["channel"].value

        no_result_response_text = translation.gettext(
            "Sorry, I can't find any channels with that name. Please try again.")

        if not channel:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        channel = channel.lower()

        channel_search_results = self.jellyfin_client.search_media_items(user_id=user.jellyfin_user_id,
                                                                       token=user.jellyfin_token,
                                                                       term=channel,
                                                                       media=MediaType.CHANNEL,
                                                                       Filters="IsNotFolder")

        if len(channel_search_results) == 0:
            # no search results
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        if len(channel_search_results) == 1:
            # there is only one search result, so just play it
            item = channel_search_results[0]
            user_id = handler_input.request_envelope.context.system.user.user_id
            playback = set_playback_queue(user_id, [PlaybackItem(item["Id"], item["Name"], [])])

            build_stream_response(jellyfin_client=self.jellyfin_client,
                                  jellyfin_user_id=user.jellyfin_user_id,
                                  jellyfin_token=user.jellyfin_token,
                                  handler_input=handler_input,
                                  playback=playback,
                                  idx=0)

            return handler_input.response_builder.response

        """
        there is more than one search result, so find the best matches like this:
             (a) sort them by match score (in descending order)
             (b) find top 3 matches and store them in session variable list
             (c) ask user to confirm their choice (see YesNoIntentHandler)
        """
        channel_match_scores = [get_similarity(item["Name"], channel) for item in channel_search_results]
        top_matches_idx = best_matches_by_idx(match_scores=channel_match_scores)
        top_matches = []
        for idx in top_matches_idx:
            match = { "Name" : channel_search_results[idx]["Name"],
                      "Id" : channel_search_results[idx]["Id"],
                      "Artist": [] }
            top_matches.append( match )
        handler_input.attributes_manager.session_attributes["TopMatches"] = top_matches

        # ask user if they want the first one...  (response is handled by YesNoIntentHandler)
        request_text = translation.gettext("Would you like to listen to {name} ?".format(
                                                                             name=top_matches[0]['Name']))

        return handler_input.response_builder.speak(request_text).ask(request_text).response
