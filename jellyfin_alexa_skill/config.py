import configparser
from pathlib import Path

DEFAULT_ALEXA_SKILL_CONFIG_PATH = "/var/lib/jellyfin_alexa_skill/config/skill.conf"
DEFAULT_ALEXA_SKILL_DATA_PATH = "/var/lib/jellyfin_alexa_skill/data"

APP_NAME = "jellyfin_alexa_skill"

CAPABILITIES_AUDIO = {
    "PlayableMediaTypes": [
        "Audio"
    ],
    "SupportedCommands": [],
    "SupportsContentUploading": False,
    "SupportsMediaControl": True,
    "SupportsPersistentIdentifier": True,
    "SupportsSync": True
}

CAPABILITIES_VIDEO = {
    "PlayableMediaTypes": [
        "Audio",
        "Video"
    ],
    "SupportedCommands": [],
    "SupportsContentUploading": False,
    "SupportsMediaControl": True,
    "SupportsPersistentIdentifier": True,
    "SupportsSync": True
}

ARTISTS_PARTIAL_RATIO_THRESHOLD = 0.7
SONG_PARTIAL_RATIO_THRESHOLD = 0.5
TITLE_PARTIAL_RATIO_THRESHOLD = 0.5


def get_config(path: Path = DEFAULT_ALEXA_SKILL_DATA_PATH) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(path)

    return config
