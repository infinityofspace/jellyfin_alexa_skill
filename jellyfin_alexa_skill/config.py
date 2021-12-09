import configparser
import gettext
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

EN_TRANSLATION = gettext.translation("skill", localedir=Path(__file__).resolve().parent / "locales", languages=("en",))
DE_TRANSLATION = gettext.translation("skill", localedir=Path(__file__).resolve().parent / "locales", languages=("de",))

TRANSLATIONS = {
    "en-US": EN_TRANSLATION,
    "de-DE": DE_TRANSLATION
}


def get_translation(language_code: str) -> gettext.GNUTranslations:
    """
    Get the translation for the given language code. If the language code is not supported, the default translation
    for locale en-US is returned.

    :param language_code: the language code

    :return: the translation
    """

    return TRANSLATIONS.get(language_code, EN_TRANSLATION)


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
