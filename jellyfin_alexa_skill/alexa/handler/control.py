from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response
from ask_sdk_model.interfaces.audioplayer import StopDirective
from rapidfuzz import fuzz

from jellyfin_alexa_skill.alexa.util import set_shuffle_queue_idxs, build_audio_stream_response
from jellyfin_alexa_skill.config import ARTISTS_PARTIAL_RATIO_THRESHOLD, SONG_PARTIAL_RATIO_THRESHOLD, \
    TITLE_PARTIAL_RATIO_THRESHOLD
from jellyfin_alexa_skill.database.db import set_playback_queue, get_playback
from jellyfin_alexa_skill.database.model.playback import PlaybackItem
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient, MediaType


class PlaySongIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlaySongIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        song = handler_input.request_envelope.request.intent.slots["song"].value
        musician = handler_input.request_envelope.request.intent.slots["musician"].value

        no_result_response_text = "Sorry I can't find any songs for this search. Please try again."

        if not song:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        song = song.lower()

        song_search_results = self.jellyfin_client.search_media_items(term=song,
                                                                      media=MediaType.AUDIO,
                                                                      Filters="IsNotFolder")

        if musician:
            musician = musician.lower()
            # filter song search results with the searched musician
            artists_search_results = self.jellyfin_client.search_artist(term=musician)
            artists_ids = set([artists["Id"] for artists in artists_search_results])

            song_search_results = [song for song in song_search_results if
                                   set(artist["Id"] for artist in song["ArtistItems"]).intersection(artists_ids)]

        song_match_scores = [fuzz.partial_ratio(item["Name"].lower(), song) for item in song_search_results]

        if song_match_scores:
            max_score = max(song_match_scores)
            if max_score >= SONG_PARTIAL_RATIO_THRESHOLD:
                item = song_search_results[song_match_scores.index(max_score)]
            else:
                handler_input.response_builder.speak(no_result_response_text)
                return handler_input.response_builder.response
        else:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        user_id = handler_input.request_envelope.context.system.user.user_id
        playback = set_playback_queue(user_id, [PlaybackItem(item["Id"], item["Name"], item["Artists"])])

        build_audio_stream_response(self.jellyfin_client, handler_input, playback, 0)

        return handler_input.response_builder.response


class PlayVideoIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayVideoIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        title = handler_input.request_envelope.request.intent.slots["title"].value
        artist = handler_input.request_envelope.request.intent.slots["artist"].value

        no_result_response_text = "Sorry I can't find any videos for this search. Please try again."

        if not title:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        title = title.lower()

        video_search_results = self.jellyfin_client.search_media_items(term=title,
                                                                       media=MediaType.VIDEO,
                                                                       Filters="IsNotFolder")

        if artist:
            artist = artist.lower()
            # filter video search results with the searched artist
            artists_search_results = self.jellyfin_client.search_artist(term=artist)
            artists_ids = set([artists["Id"] for artists in artists_search_results])

            video_search_results = [song for song in video_search_results if
                                    set(artist["Id"] for artist in song["ArtistItems"]).intersection(artists_ids)]

        video_match_scores = [fuzz.partial_ratio(item["Name"].lower(), title) for item in video_search_results]

        if video_match_scores:
            max_score = max(video_match_scores)
            if max_score >= TITLE_PARTIAL_RATIO_THRESHOLD:
                item = video_search_results[video_match_scores.index(max_score)]
            else:
                handler_input.response_builder.speak(no_result_response_text)
                return handler_input.response_builder.response
        else:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        user_id = handler_input.request_envelope.context.system.user.user_id
        playback = set_playback_queue(user_id, [PlaybackItem(item["Id"], item["Name"], item["Artists"])])

        build_audio_stream_response(self.jellyfin_client, handler_input, playback, 0)

        return handler_input.response_builder.response


class PlaySongsArtistIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlaySongsArtistIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        musician = handler_input.request_envelope.request.intent.slots["musician"].value

        no_result_response_text = "Sorry I can't find any songs with this artist. Please try again."

        if not musician:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        musician = musician.lower()

        search_results = self.jellyfin_client.search_artist(term=musician)

        song_match_scores = [fuzz.partial_ratio(item["Name"].lower(), musician) for item in search_results]

        best_score = max(song_match_scores)
        if best_score < ARTISTS_PARTIAL_RATIO_THRESHOLD:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        artist_item = search_results[song_match_scores.index(best_score)]
        artist_id = artist_item["Id"]

        items = self.jellyfin_client.get_artist_items(artist_id, media=MediaType.AUDIO)

        playback_items = [PlaybackItem(item["Id"], item["Name"], item["Artists"])
                          for item in items]

        user_id = handler_input.request_envelope.context.system.user.user_id
        playback = set_playback_queue(user_id, playback_items)

        build_audio_stream_response(self.jellyfin_client, handler_input, playback, 0)

        return handler_input.response_builder.response


class PlayVideosArtistIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayVideosArtistIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        artist = handler_input.request_envelope.request.intent.slots["artist"].value

        no_result_response_text = "Sorry I can't find any videos with this artist. Please try again."

        if not artist:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        artist = artist.lower()

        search_results = self.jellyfin_client.search_artist(term=artist)

        song_match_scores = [fuzz.partial_ratio(item["Name"].lower(), artist) for item in search_results]

        best_score = max(song_match_scores)
        if best_score < ARTISTS_PARTIAL_RATIO_THRESHOLD:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        artist_item = search_results[song_match_scores.index(best_score)]
        artist_id = artist_item["Id"]

        items = self.jellyfin_client.get_artist_items(artist_id, media=MediaType.VIDEO)

        playback_items = [PlaybackItem(item["Id"], item["Name"], item["Artists"])
                          for item in items]

        user_id = handler_input.request_envelope.context.system.user.user_id
        playback = set_playback_queue(user_id, playback_items)

        build_audio_stream_response(self.jellyfin_client, handler_input, playback, 0)

        return handler_input.response_builder.response


class PlayLastAddedIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayLastAddedIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        recently_added_items = self.jellyfin_client.jellyfin.get_recently_added(limit=50)

        if len(recently_added_items) == 0:
            text = "Sorry, I couldn't find any recently added media."
            handler_input.response_builder.speak(text)
        else:
            playback_items = [PlaybackItem(item["Id"], item["Name"], item["Artists"])
                              for item in recently_added_items]

            playback = set_playback_queue(handler_input.request_envelope.session.user.user_id, playback_items)

            build_audio_stream_response(self.jellyfin_client, handler_input, playback, 0)

        return handler_input.response_builder.response


class PlayLastAddedVideosIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayLastAddedVideosIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        recently_added_items = self.jellyfin_client.jellyfin.get_recently_added(media="Video", limit=50)

        if len(recently_added_items) == 0:
            text = "Sorry, I couldn't find any recently added videos."
            handler_input.response_builder.speak(text)
        else:
            playback_items = [PlaybackItem(item["Id"], item["Name"], item["Artists"])
                              for item in recently_added_items]

            playback = set_playback_queue(handler_input.request_envelope.session.user.user_id, playback_items)

            build_audio_stream_response(self.jellyfin_client, handler_input, playback, 0)

        return handler_input.response_builder.response


class PlayLastAddedSongsIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayLastAddedSongsIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        recently_added_items = self.jellyfin_client.jellyfin.get_recently_added(media="Audio", limit=50)

        if recently_added_items:
            playback_items = [PlaybackItem(item["Id"], item["Name"], item["Artists"])
                              for item in recently_added_items]

            playback = set_playback_queue(handler_input.request_envelope.session.user.user_id, playback_items)

            build_audio_stream_response(self.jellyfin_client, handler_input, playback, 0)
        else:
            text = "Sorry, I couldn't find any recently added songs."
            handler_input.response_builder.speak(text)

        return handler_input.response_builder.response


class PauseIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.PauseIntent")(handler_input) \
               or is_intent_name("AMAZON.StopIntent")(handler_input) \
               or is_intent_name("AMAZON.CancelIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        playback.playing = False
        playback.offset = handler_input.request_envelope.context.audio_player.offset_in_milliseconds
        playback.save()

        handler_input.response_builder.add_directive(StopDirective())

        return handler_input.response_builder.response


class ResumeIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.ResumeIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        if playback.current_idx < len(playback.queue):
            build_audio_stream_response(self.jellyfin_client, handler_input, playback, 0)
        else:
            text = "What can I play?"
            handler_input.response_builder.add_directive(StopDirective()).speak(text)

        return handler_input.response_builder.response


class LoopAllOffIntent(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("LoopAllOffIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        playback.loop_all = False
        playback.loop_single = False
        playback.save()

        return handler_input.response_builder.response


class LoopAllOnIntent(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("LoopAllOnIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        playback.loop_all = True
        playback.save()

        return handler_input.response_builder.response


class NextIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.NextIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)

        if playback.queue and (playback.current_idx + 1 < len(playback.queue) or playback.loop_all):
            playback.current_idx = (playback.current_idx + 1) % len(playback.queue)
            playback.save()

            build_audio_stream_response(self.jellyfin_client, handler_input, playback, playback.current_idx)
        else:
            if playback.current_idx + 1 >= len(playback.queue):
                text = "You reached the end of the playback queue."
                handler_input.response_builder.add_directive(StopDirective()).speak(text)
            else:
                handler_input.response_builder.add_directive(StopDirective())

        return handler_input.response_builder.response


class PreviousIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.PreviousIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)

        if playback.queue and (playback.current_idx > 0 or playback.loop_all):
            playback.current_idx = (playback.current_idx - 1) % len(playback.queue)
            playback.save()

            build_audio_stream_response(self.jellyfin_client, handler_input, playback, playback.current_idx)
        else:
            if playback.current_idx == 0:
                text = "You reached the start of the playback queue."
                handler_input.response_builder.add_directive(StopDirective()).speak(text)
            else:
                handler_input.response_builder.add_directive(StopDirective())

        return handler_input.response_builder.response


class RepeatSingleOnIntent(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("RepeatSingleOnIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        playback.loop_single = True
        playback.save()

        return handler_input.response_builder.response


class ShuffleOffIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.ShuffleOffIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        playback.shuffle = False
        playback.shuffle_idxs = []
        playback.save()

        return handler_input.response_builder.response


class ShuffleOnIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.ShuffleOnIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)

        playback.shuffle = True
        set_shuffle_queue_idxs(playback)
        playback.save()

        return handler_input.response_builder.response


class StartOverIntentHandler(AbstractRequestHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.StartOverIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)

        if playback.queue:
            build_audio_stream_response(self.jellyfin_client, handler_input, playback, playback.current_idx)
        else:
            text = "The playback queue is empty. Please try to add some media and try again."
            handler_input.response_builder.add_directive(StopDirective()).speak(text)

        return handler_input.response_builder.response
