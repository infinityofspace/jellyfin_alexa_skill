import gettext
from pathlib import Path

from jellyfin_alexa_skill.config import SUPPORTED_LANGUAGES

TRANSLATIONS = {}

for language in SUPPORTED_LANGUAGES:
    TRANSLATIONS[language] = gettext.translation("skill",
                                                 localedir=Path(__file__).resolve().parent / "locales",
                                                 languages=(language.replace("-", "_"),))

DEFAULT_LANGUAGE = "en-US"


def get_translation(language_code: str) -> gettext.GNUTranslations:
    """
    Get the translation for the given language code. If the language code is not supported, the default translation
    for locale en-US is returned.

    :param language_code: the language code

    :return: the translation
    """

    return TRANSLATIONS.get(language_code, DEFAULT_LANGUAGE)
