from gettext import GNUTranslations

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response
from ask_sdk_model.interfaces.audioplayer import StopDirective

from jellyfin_alexa_skill.alexa.handler.base import BaseHandler
from jellyfin_alexa_skill.alexa.util import set_shuffle_queue_idxs, build_stream_response, MediaTypeSlot, translate, \
    get_similarity
from jellyfin_alexa_skill.config import ARTISTS_PARTIAL_RATIO_THRESHOLD, SONG_PARTIAL_RATIO_THRESHOLD, \
    TITLE_PARTIAL_RATIO_THRESHOLD
from jellyfin_alexa_skill.database.db import set_playback_queue, get_playback
from jellyfin_alexa_skill.database.model.playback import PlaybackItem
from jellyfin_alexa_skill.database.model.user import User
from jellyfin_alexa_skill.jellyfin.api.client import MediaType, JellyfinClient


class PlaySongIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlaySongIntent")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        song = handler_input.request_envelope.request.intent.slots["song"].value
        musician = handler_input.request_envelope.request.intent.slots["musician"].value

        no_result_response_text = translation.gettext(
            "Sorry, I can't find any songs for this search. Please try again.")

        if not song:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        song = song.lower()

        song_search_results = self.jellyfin_client.search_media_items(user_id=user.jellyfin_user_id,
                                                                      token=user.jellyfin_token,
                                                                      term=song,
                                                                      media=MediaType.AUDIO,
                                                                      Filters="IsNotFolder")

        if musician:
            musician = musician.lower()
            # filter song search results with the searched musician
            artists_search_results = self.jellyfin_client.search_artist(user_id=user.jellyfin_user_id,
                                                                        token=user.jellyfin_token,
                                                                        term=musician)
            artists_ids = set([artists["Id"] for artists in artists_search_results])

            song_search_results = [song for song in song_search_results if
                                   set(artist["Id"] for artist in song["ArtistItems"]).intersection(artists_ids)]

        song_match_scores = [get_similarity(item["Name"], song) for item in song_search_results]

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

        build_stream_response(jellyfin_client=self.jellyfin_client,
                              jellyfin_user_id=user.jellyfin_user_id,
                              jellyfin_token=user.jellyfin_token,
                              handler_input=handler_input,
                              playback=playback,
                              idx=0)

        return handler_input.response_builder.response


class PlayVideoIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayVideoIntent")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        title = handler_input.request_envelope.request.intent.slots["title"].value

        no_result_response_text = translation.gettext(
            "Sorry, I can't find any videos for this search. Please try again.")

        if not title:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        title = title.lower()

        video_search_results = self.jellyfin_client.search_media_items(user_id=user.jellyfin_user_id,
                                                                       token=user.jellyfin_token,
                                                                       term=title,
                                                                       media=MediaType.VIDEO,
                                                                       Filters="IsNotFolder")

        video_match_scores = [get_similarity(item["Name"], title) for item in video_search_results]

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
        playback = set_playback_queue(user_id, [PlaybackItem(item["Id"], item["Name"], [])])

        build_stream_response(jellyfin_client=self.jellyfin_client,
                              jellyfin_user_id=user.jellyfin_user_id,
                              jellyfin_token=user.jellyfin_token,
                              handler_input=handler_input,
                              playback=playback,
                              idx=0)

        return handler_input.response_builder.response


class PlayArtistSongsIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayArtistSongsIntent")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        musician = handler_input.request_envelope.request.intent.slots["musician"].value

        no_result_response_text = translation.gettext(
            "Sorry, I can't find any songs with this artist. Please try again.")

        if not musician:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        musician = musician.lower()

        search_results = self.jellyfin_client.search_artist(user_id=user.jellyfin_user_id,
                                                            token=user.jellyfin_token,
                                                            term=musician)

        song_match_scores = [get_similarity(item["Name"], musician) for item in search_results]

        if not song_match_scores:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        best_score = max(song_match_scores)
        if best_score < ARTISTS_PARTIAL_RATIO_THRESHOLD:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        artist_item = search_results[song_match_scores.index(best_score)]
        artist_id = artist_item["Id"]

        items = self.jellyfin_client.get_artist_items(user_id=user.jellyfin_user_id,
                                                      token=user.jellyfin_token,
                                                      artist_id=artist_id,
                                                      media=MediaType.AUDIO)

        if not items:
            handler_input.response_builder.speak(no_result_response_text)
            return handler_input.response_builder.response

        playback_items = [PlaybackItem(item["Id"], item["Name"], item["Artists"])
                          for item in items]

        user_id = handler_input.request_envelope.context.system.user.user_id
        playback = set_playback_queue(user_id, playback_items)

        build_stream_response(jellyfin_client=self.jellyfin_client,
                              jellyfin_user_id=user.jellyfin_user_id,
                              jellyfin_token=user.jellyfin_token,
                              handler_input=handler_input,
                              playback=playback,
                              idx=0)

        return handler_input.response_builder.response


class PlayLastAddedIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("PlayLastAddedIntent")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        media_type = handler_input.request_envelope.request.intent.slots["media_type"] \
            .resolutions.resolutions_per_authority[0].values[0].value.id

        if media_type == MediaTypeSlot.AUDIO:
            filter_media_type = MediaType.AUDIO
        elif media_type == MediaTypeSlot.VIDEO:
            filter_media_type = MediaType.VIDEO
        else:
            filter_media_type = None

        recently_added_items = self.jellyfin_client.get_recently_added(user_id=user.jellyfin_user_id,
                                                                       token=user.jellyfin_token,
                                                                       media=filter_media_type,
                                                                       limit=50)

        if len(recently_added_items) == 0:
            text = translation.gettext("Sorry, I couldn't find any recently added media.")
            handler_input.response_builder.speak(text)
        else:
            playback_items = [PlaybackItem(item["Id"], item["Name"], item.get("Artists", []))
                              for item in recently_added_items]

            playback = set_playback_queue(handler_input.request_envelope.session.user.user_id, playback_items)

            build_stream_response(jellyfin_client=self.jellyfin_client,
                                  jellyfin_user_id=user.jellyfin_user_id,
                                  jellyfin_token=user.jellyfin_token,
                                  handler_input=handler_input,
                                  playback=playback,
                                  idx=0)

        return handler_input.response_builder.response


class PauseIntentHandler(BaseHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.PauseIntent")(handler_input) \
               or is_intent_name("AMAZON.StopIntent")(handler_input) \
               or is_intent_name("AMAZON.CancelIntent")(handler_input)

    def handle_func(self, user: User, handler_input: HandlerInput, *args, **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        playback.playing = False
        playback.offset = handler_input.request_envelope.context.audio_player.offset_in_milliseconds
        playback.save()

        handler_input.response_builder.add_directive(StopDirective())

        return handler_input.response_builder.response


class ResumeIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.ResumeIntent")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        if playback.current_idx < len(playback.queue):
            build_stream_response(jellyfin_client=self.jellyfin_client,
                                  jellyfin_user_id=user.jellyfin_user_id,
                                  jellyfin_token=user.jellyfin_token,
                                  handler_input=handler_input,
                                  playback=playback,
                                  idx=playback.current_idx)
        else:
            text = translation.gettext("What can I play?")
            handler_input.response_builder.add_directive(StopDirective()).speak(text)

        return handler_input.response_builder.response


class LoopAllOffIntent(BaseHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("LoopAllOffIntent")(handler_input)

    def handle_func(self, user: User, handler_input: HandlerInput, *args, **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        playback.loop_all = False
        playback.loop_single = False
        playback.save()

        return handler_input.response_builder.response


class LoopAllOnIntent(BaseHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("LoopAllOnIntent")(handler_input)

    def handle_func(self, user: User, handler_input: HandlerInput, *args, **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        playback.loop_all = True
        playback.save()

        return handler_input.response_builder.response


class NextIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.NextIntent")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)

        if playback.queue and (playback.current_idx + 1 < len(playback.queue) or playback.loop_all):
            playback.current_idx = (playback.current_idx + 1) % len(playback.queue)
            playback.save()

            build_stream_response(jellyfin_client=self.jellyfin_client,
                                  jellyfin_user_id=user.jellyfin_user_id,
                                  jellyfin_token=user.jellyfin_token,
                                  handler_input=handler_input,
                                  playback=playback,
                                  idx=playback.current_idx)
        else:
            if playback.current_idx + 1 >= len(playback.queue):
                text = translation.gettext("You reached the end of the playback queue.")
                handler_input.response_builder.add_directive(StopDirective()).speak(text)
            else:
                handler_input.response_builder.add_directive(StopDirective())

        return handler_input.response_builder.response


class PreviousIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.PreviousIntent")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)

        if playback.queue and (playback.current_idx > 0 or playback.loop_all):
            playback.current_idx = (playback.current_idx - 1) % len(playback.queue)
            playback.save()

            build_stream_response(jellyfin_client=self.jellyfin_client,
                                  jellyfin_user_id=user.jellyfin_user_id,
                                  jellyfin_token=user.jellyfin_token,
                                  handler_input=handler_input,
                                  playback=playback,
                                  idx=playback.current_idx)
        else:
            if playback.current_idx == 0:
                text = translation.gettext("You reached the start of the playback queue.")
                handler_input.response_builder.add_directive(StopDirective()).speak(text)
            else:
                handler_input.response_builder.add_directive(StopDirective())

        return handler_input.response_builder.response


class RepeatSingleOnIntent(BaseHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("RepeatSingleOnIntent")(handler_input)

    def handle_func(self, user: User, handler_input: HandlerInput, *args, **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        playback.loop_single = True
        playback.save()

        return handler_input.response_builder.response


class ShuffleOffIntentHandler(BaseHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.ShuffleOffIntent")(handler_input)

    def handle_func(self, user: User, handler_input: HandlerInput, *args, **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)
        playback.shuffle = False
        playback.shuffle_idxs = []
        playback.save()

        return handler_input.response_builder.response


class ShuffleOnIntentHandler(BaseHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.ShuffleOnIntent")(handler_input)

    def handle_func(self, user: User, handler_input: HandlerInput, *args, **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)

        playback.shuffle = True
        set_shuffle_queue_idxs(playback)
        playback.save()

        return handler_input.response_builder.response


class StartOverIntentHandler(BaseHandler):
    def __init__(self, jellyfin_client: JellyfinClient):
        self.jellyfin_client = jellyfin_client

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.StartOverIntent")(handler_input)

    @translate
    def handle_func(self,
                    user: User,
                    handler_input: HandlerInput,
                    translation: GNUTranslations,
                    *args,
                    **kwargs) -> Response:
        user_id = handler_input.request_envelope.context.system.user.user_id

        playback = get_playback(user_id)

        if playback.queue:
            build_stream_response(jellyfin_client=self.jellyfin_client,
                                  jellyfin_user_id=user.jellyfin_user_id,
                                  jellyfin_token=user.jellyfin_token,
                                  handler_input=handler_input,
                                  playback=playback,
                                  idx=playback.current_idx)
        else:
            text = translation.gettext("The playback queue is empty. Please try to add some media and try again.")
            handler_input.response_builder.add_directive(StopDirective()).speak(text)

        return handler_input.response_builder.response
