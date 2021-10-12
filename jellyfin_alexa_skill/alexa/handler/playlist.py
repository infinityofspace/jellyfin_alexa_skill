from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response
from rapidfuzz import fuzz

from jellyfin_alexa_skill.alexa.util import build_audio_stream_response
from jellyfin_alexa_skill.database.db import set_playback_queue
from jellyfin_alexa_skill.database.model.playback import PlaybackItem
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient


class PlayPlaylistIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayPlaylistIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.session.user.user_id

        playlist_name = handler_input.request_envelope.request.intent.slots["playlist"].value
        playlists = self.jellyfin_client.get_playlist(playlist_name)

        if not playlists:
            text = "Sorry I couldn't find any playlist with this name. Please try again."
            handler_input.response_builder.speak(text)
        else:
            # try to find the best playlist name match
            match_scores = [fuzz.partial_ratio(item["Name"], playlist_name) for item in playlists]
            best_playlist = playlists[match_scores.index(max(match_scores))]

            playlist_items = self.jellyfin_client.get_playlist_items(best_playlist["Id"])

            if not playlist_items:
                text = "Sorry this playlist does not exists anymore."
                handler_input.response_builder.speak(text)
            else:
                playback_items = [PlaybackItem(item["Id"], item["Name"], item["Artists"])
                                  for item in playlist_items]

                playback = set_playback_queue(user_id, playback_items)

                build_audio_stream_response(self.jellyfin_client, handler_input, playback, playback.current_idx)

                handler_input.response_builder.speak(f"Ok, I play the playlist {best_playlist['Name']}")

        return handler_input.response_builder.response
