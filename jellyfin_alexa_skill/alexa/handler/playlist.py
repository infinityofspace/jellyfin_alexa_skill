from gettext import GNUTranslations

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response

from jellyfin_alexa_skill.alexa.handler import BaseHandler
from jellyfin_alexa_skill.alexa.util import build_stream_response, translate, get_similarity
from jellyfin_alexa_skill.database.db import set_playback_queue
from jellyfin_alexa_skill.database.model.playback import PlaybackItem
from jellyfin_alexa_skill.database.model.user import User
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient


class PlayPlaylistIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayPlaylistIntent")(handler_input)

    @translate
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
                playback_items = [PlaybackItem(item["Id"], item["Name"], item["Artists"])
                                  for item in playlist_items]

                playback = set_playback_queue(user_id, playback_items)

                build_stream_response(jellyfin_client=self.jellyfin_client,
                                      jellyfin_user_id=user.jellyfin_user_id,
                                      jellyfin_token=user.jellyfin_token,
                                      handler_input=handler_input,
                                      playback=playback,
                                      idx=0)

                handler_input.response_builder.speak(_("Ok, I play the playlist {}.".format(best_playlist["Name"])))

        return handler_input.response_builder.response
