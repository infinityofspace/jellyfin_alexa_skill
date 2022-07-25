from gettext import GNUTranslations

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.handler import BaseHandler
from jellyfin_alexa_skill.alexa.util import build_stream_response, get_similarity, get_media_type_enum
from jellyfin_alexa_skill.database.db import get_playback
from jellyfin_alexa_skill.database.model.playback import QueueItem
from jellyfin_alexa_skill.database.model.user import User
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient


class PlayPlaylistIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayPlaylistIntent")(handler_input)

    @BaseHandler.translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        user_id = handler_input.request_envelope.session.user.user_id

        playlist_name = handler_input.request_envelope.request.intent.slots["playlist"].value
        playlists = self.jellyfin_client.get_playlist(user_id=user.jellyfin_user_id,
                                                      token=user.jellyfin_token,
                                                      playlist_name=playlist_name)

        if not playlists:
            text = translation.gettext("Sorry, I couldn't find any playlist with this name. Please try again.")
            handler_input.response_builder.speak(text)
        else:
            # try to find the best playlist name match
            match_scores = [get_similarity(item["Name"], playlist_name) for item in playlists]
            best_playlist = playlists[match_scores.index(max(match_scores))]

            playlist_items = self.jellyfin_client.get_playlist_items(user_id=user.jellyfin_user_id,
                                                                     token=user.jellyfin_token,
                                                                     playlist_id=best_playlist["Id"])

            if not playlist_items:
                text = translation.gettext("Sorry, this playlist does not exists anymore.")
                handler_input.response_builder.speak(text)
            else:
                queue_items = [QueueItem(idx=i,
                                         media_type=get_media_type_enum(item_info),
                                         media_item_id=item_info["Id"]) for i, item_info in
                               enumerate(playlist_items)]

                playback = get_playback(user_id)
                playback.set_queue(queue_items)

                build_stream_response(jellyfin_client=self.jellyfin_client,
                                      jellyfin_user_id=user.jellyfin_user_id,
                                      jellyfin_token=user.jellyfin_token,
                                      handler_input=handler_input,
                                      queue_item=playback.current_item)

                response_text = translation.gettext("Ok, I play the playlist {}.").format(best_playlist["Name"])
                handler_input.response_builder.speak(response_text)

        return handler_input.response_builder.response
