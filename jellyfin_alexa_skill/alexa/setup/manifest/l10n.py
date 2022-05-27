import gettext
import importlib.resources as pkg_resources
from pathlib import Path

from ask_sdk_core.serialize import DefaultSerializer
from ask_smapi_model.v1.skill.manifest import SkillManifestEnvelope

from jellyfin_alexa_skill import __file__ as package_root
from jellyfin_alexa_skill.alexa.setup import manifest as manifest_module
from jellyfin_alexa_skill.config import SUPPORTED_LANGUAGES

DEFAULT_LANGUAGE = "en-US"


def build_pot_file_str() -> str:
    manifest = DefaultSerializer().deserialize(pkg_resources.read_text(manifest_module, "manifest.json"),
                                               SkillManifestEnvelope)

    en_US_locale = manifest.manifest.publishing_information.locales["en-US"]

    summary = en_US_locale.summary.replace("\n", "</br>")

    description = en_US_locale.description.replace("\n", "</br>")

    pot_file_str = "msgid \"\"\n" \
                   "msgstr \"\"\n" \
                   "\n" \
                   "#: summary\n" \
                   f"msgid \"{summary}\"\n" \
                   f"msgstr \"\"\n" \
                   "\n" \
                   "#: description\n" \
                   f"msgid \"{description}\"\n" \
                   f"msgstr \"\"\n" \
                   "\n"

    for phrase in en_US_locale.example_phrases:
        phrase = phrase.replace("\n", "</br>")

        pot_file_str += "#: example phrase\n" \
                        f"msgid \"{phrase}\"\n" \
                        f"msgstr \"\"\n\n"

    return pot_file_str


def internationalize_manifest(manifest: SkillManifestEnvelope) -> None:
    translations = {}

    locales_path = Path(package_root).parent / "locales"

    for language in SUPPORTED_LANGUAGES:
        translations[language] = gettext.translation("manifest",
                                                     localedir=locales_path,
                                                     languages=(language.replace("-", "_"),))

    en_US_locale = manifest.manifest.publishing_information.locales["en-US"]

    # localize the manifest
    for lang in SUPPORTED_LANGUAGES:
        translation = translations.get(lang, DEFAULT_LANGUAGE)

        locale = {
            "name": "Jellyfin Player",
            "summary": translation.gettext(en_US_locale.summary.replace("</br>", "\n")),
            "examplePhrases": [
                translation.gettext(phrase.replace("</br>", "\n")) for phrase in en_US_locale.example_phrases
            ],
            "description": translation.gettext(en_US_locale.description.replace("</br>", "\n")),
        }
        manifest.manifest.publishing_information.locales[lang] = locale
