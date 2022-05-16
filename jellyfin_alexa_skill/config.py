import configparser
import gettext
import ipaddress
import re
from pathlib import Path
from typing import Union

from jellyfin_alexa_skill.utils import validate_url, Protocols

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
IT_TRANSLATION = gettext.translation("skill", localedir=Path(__file__).resolve().parent / "locales", languages=("it",))
ES_TRANSLATION = gettext.translation("skill", localedir=Path(__file__).resolve().parent / "locales", languages=("es",))

TRANSLATIONS = {
    "en-US": EN_TRANSLATION,
    "de-DE": DE_TRANSLATION,
    "it-IT": IT_TRANSLATION,
    "es-ES": ES_TRANSLATION,
}


def get_translation(language_code: str) -> gettext.GNUTranslations:
    """
    Get the translation for the given language code. If the language code is not supported, the default translation
    for locale en-US is returned.

    :param language_code: the language code

    :return: the translation
    """

    return TRANSLATIONS.get(language_code, EN_TRANSLATION)


def get_config(path: Path) -> configparser.ConfigParser:
    """
    Get the configuration from the given path.

    :param path: the path to the configuration file

    :return: the configuration
    """

    config = configparser.ConfigParser()
    config.read(path)

    validate_config(config)

    return config


def write_config(config_path: Union[Path, str], config: configparser.ConfigParser) -> None:
    """
    Write the configuration to the given path.

    :param config_path: the path to the configuration file
    :param config: the configuration which should be written
    """

    with open(str(config_path), "w") as f:
        config.write(f)


def validate_config(config: configparser.ConfigParser) -> None:
    """
    Validate the configuration file.

    :param config: the configuration parser
    :raises: Exception if the configuration is invalid
    """

    skill_endpoint = config.get("general", "skill_endpoint", fallback="")
    if not validate_url(skill_endpoint, proto=Protocols.HTTPS):
        raise ValueError(f"Invalid skill endpoint \"{skill_endpoint}\"")

    jellyfin_endpoint = config.get("general", "jellyfin_endpoint", fallback="")
    if not validate_url(jellyfin_endpoint, proto=Protocols.HTTPS):
        raise ValueError(f"Invalid jellyfin endpoint \"{jellyfin_endpoint}\"")

    host = config.get("general", "bind_addr", fallback="0.0.0.0")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        raise ValueError(f"Invalid host address \"{host}\"")

    web_app_port = config.getint("general", "web_app_port", fallback=1456)
    if web_app_port < 1 or web_app_port > 65535:
        raise ValueError(f"Invalid web app port \"{web_app_port}\"")

    if len(config.get("smapi", "client_id", fallback="").strip()) == 0:
        raise ValueError("SMAPI client ID is not set")
    if len(config.get("smapi", "client_secret", fallback="").strip()) == 0:
        raise ValueError("SMAPI client secret is not set")
    if len(config.get("smapi", "refresh_token", fallback="").strip()) == 0:
        raise ValueError("SMAPI refresh token is not set")

    if len(config.get("general", "skill_id", fallback="").strip()) == 0:
        raise ValueError("Skill ID is not set")

    if len(config.get("database", "password", fallback="").strip()) == 0:
        raise ValueError("Database password is not set")
