from gettext import GNUTranslations

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.handler.base import BaseHandler
from jellyfin_alexa_skill.alexa.util import build_stream_response, MediaTypeSlot, translate, get_similarity, best_matches_by_idx
from jellyfin_alexa_skill.config import TITLE_PARTIAL_RATIO_THRESHOLD, use_generous_search
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

        if not channel_search_results:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        channel_match_scores = [get_similarity(item["Name"], channel) for item in channel_search_results]

        if use_generous_search():
            """
            generous search: choose the best option from the returned results.
                             match scores are used to rank results, but not as a filter.

                * if there is just one result, then use it (even if it has a low match score)
                * if there is >1 result, then: (a) sort them by match score
                                               (b) loop through top 3 matches and ask user to confirm the choice
                                               (c) if user confirms, use that item
                                               (d) if user rejects all top 3 matches ==> no match
            """
            if len(channel_search_results) == 1:
                item = channel_search_results[0]
            else:
                # more than 1 result, so we need to find the best results and start a yes/no dialog with user

                # get list of top matches (sorted in descending order of match score) and store as session variable list
                top_matches_idx = best_matches_by_idx(match_scores=channel_match_scores)
                top_matches = []
                for idx in top_matches_idx:
                    match = { "Name" : channel_search_results[idx]["Name"],
                              "Id" : channel_search_results[idx]["Id"],
                              "Artist": [] }
                    top_matches.append( match )
                handler_input.attributes_manager.session_attributes["TopMatches"] = top_matches

                # ask user if they want the first one...  (response is handled by YesNoIntentHandler)
                request_text = f"Would you like to listen to {channel_search_results[0]['Name']} ?"
                return handler_input.response_builder.speak(request_text).ask(request_text).response

        else:
            # choose the item with biggest match score.  Ignore items with match scores less than TITLE_PARTIAL_RATIO_THRESHOLD.
            max_score = max(channel_match_scores)
            if max_score >= TITLE_PARTIAL_RATIO_THRESHOLD:
                item = channel_search_results[channel_match_scores.index(max_score)]
            else:
                handler_input.response_builder.speak(no_result_response_text)
                return handler_input.response_builder.response

        user_id = handler_input.request_envelope.context.system.user.user_id
        playback = set_playback_queue(user_id, [PlaybackItem(item["Id"], item["Name"], [])])

        build_stream_response(jellyfin_client=self.jellyfin_client,
                              jellyfin_user_id=user.jellyfin_user_id,
                              jellyfin_token=user.jellyfin_token,
                              handler_input=handler_input,
                              playback=playback,
                              idx=0)

        return handler_input.response_builder.response
