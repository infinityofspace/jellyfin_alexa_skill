import configparser
import gettext
import re
from pathlib import Path

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
    "https://((alexa)|(layla)|(pitangui))\.amazon\.com/spa/skill/account-linking-status\.html\?vendorId=.+"
)

EN_TRANSLATION = gettext.translation("skill", localedir=Path(__file__).resolve().parent / "locales", languages=("en",))
DE_TRANSLATION = gettext.translation("skill", localedir=Path(__file__).resolve().parent / "locales", languages=("de",))


def get_translation(language_code: str) -> gettext.GNUTranslations:
    if language_code == "de-DE":
        return DE_TRANSLATION
    else:
        return EN_TRANSLATION


def get_config(path: Path = DEFAULT_ALEXA_SKILL_DATA_PATH) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(path)

    return config
