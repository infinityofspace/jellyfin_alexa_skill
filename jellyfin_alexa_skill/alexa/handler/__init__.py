from ask_sdk_core.skill_builder import SkillBuilder

from jellyfin_alexa_skill.alexa.handler.control import *
from jellyfin_alexa_skill.alexa.handler.error import CatchAllExceptionHandler
from jellyfin_alexa_skill.alexa.handler.event import *
from jellyfin_alexa_skill.alexa.handler.fallback import *
from jellyfin_alexa_skill.alexa.handler.favorite import *
from jellyfin_alexa_skill.alexa.handler.help import *
from jellyfin_alexa_skill.alexa.handler.info import *
from jellyfin_alexa_skill.alexa.handler.launch import *
from jellyfin_alexa_skill.alexa.handler.playlist import *


def get_skill_builder(jellyfin_client: JellyfinClient):
    skill_builder = SkillBuilder()

    skill_builder.add_request_handler(FallbackIntentHandler())
    skill_builder.add_exception_handler(CatchAllExceptionHandler())

    skill_builder.add_request_handler(LaunchRequestHandler(jellyfin_client))
    skill_builder.add_request_handler(CheckAudioInterfaceHandler())
    skill_builder.add_request_handler(SessionEndedRequestHandler())

    skill_builder.add_request_handler(PlaySongIntentHandler(jellyfin_client))
    skill_builder.add_request_handler(PlayVideoIntentHandler(jellyfin_client))
    skill_builder.add_request_handler(PlayArtistSongsIntentHandler(jellyfin_client))

    skill_builder.add_request_handler(PlayLastAddedIntentHandler(jellyfin_client))

    skill_builder.add_request_handler(PauseIntentHandler())
    skill_builder.add_request_handler(ResumeIntentHandler(jellyfin_client))

    skill_builder.add_request_handler(LoopAllOffIntent())
    skill_builder.add_request_handler(LoopAllOnIntent())
    skill_builder.add_request_handler(NextIntentHandler(jellyfin_client))
    skill_builder.add_request_handler(PreviousIntentHandler(jellyfin_client))
    skill_builder.add_request_handler(RepeatSingleOnIntent())
    skill_builder.add_request_handler(ShuffleOffIntentHandler())
    skill_builder.add_request_handler(ShuffleOnIntentHandler())
    skill_builder.add_request_handler(StartOverIntentHandler(jellyfin_client))

    skill_builder.add_request_handler(PlayFavoritesIntentHandler(jellyfin_client))
    skill_builder.add_request_handler(MarkFavoriteIntentHandler(jellyfin_client))
    skill_builder.add_request_handler(UnmarkFavoriteIntentHandler(jellyfin_client))

    skill_builder.add_request_handler(PlayPlaylistIntentHandler(jellyfin_client))

    skill_builder.add_request_handler(PlaybackStartedEventHandler())
    skill_builder.add_request_handler(PlaybackStoppedEventHandler())
    skill_builder.add_request_handler(PlaybackFinishedEventHandler())
    skill_builder.add_request_handler(PlaybackNearlyFinishedEventHandler(jellyfin_client))
    skill_builder.add_request_handler(PlaybackFailedEventHandler())

    skill_builder.add_request_handler(MediaInfoIntentHandler())
    skill_builder.add_request_handler(HelpIntentHandler())

    return skill_builder
