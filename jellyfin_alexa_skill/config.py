import configparser
import re
from pathlib import Path
from typing import Union

DEFAULT_ALEXA_SKILL_CONFIG_PATH = str(Path.home() / ".jellyfin_alexa_skill/config/skill.conf")
DEFAULT_ALEXA_SKILL_DATA_PATH = str(Path.home() / ".jellyfin_alexa_skill/data")

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

VALID_ALEXA_REDIRECT_URLS_REGEX = re.compile(
    r"https://((pitangui|layla)\.amazon\.com|alexa\.amazon\.co\.jp)/spa/skill/account-linking-status\.html\?vendorId=.+"
)

SUPPORTED_LANGUAGES = [
    "ar-SA",
    "de-DE",
    "en-AU",
    "en-CA",
    "en-GB",
    "en-IN",
    "en-US",
    "es-ES",
    "es-MX",
    "es-US",
    "fr-CA",
    "fr-FR",
    "hi-IN",
    "it-IT",
    "ja-JP",
    "pt-BR"
]


def get_config(path: Path = DEFAULT_ALEXA_SKILL_DATA_PATH) -> configparser.ConfigParser:
    """
    Get the configuration from the given path.

    :param path: the path to the configuration file

    :return: the configuration
    """

    config = configparser.ConfigParser()
    config.read(path)

    return config


def write_config(config_path: Union[Path, str], config: configparser.ConfigParser) -> None:
    """
    Write the configuration to the given path.

    :param config_path: the path to the configuration file
    :param config: the configuration which should be written
    """

    with open(str(config_path), "w") as f:
        config.write(f)
