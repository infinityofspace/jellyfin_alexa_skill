import gettext
import importlib.resources as pkg_resources
from copy import deepcopy
from pathlib import Path
from typing import Dict

from ask_sdk_model_runtime import DefaultSerializer
from ask_smapi_model.v1.skill.interaction_model import InteractionModelData

from jellyfin_alexa_skill import __file__ as package_root
from jellyfin_alexa_skill.alexa.setup import interaction
from jellyfin_alexa_skill.config import SUPPORTED_LANGUAGES

DEFAULT_LANGUAGE = "en-US"


def build_pot_file_str() -> str:
    INTERACTION_MODEL = DefaultSerializer().deserialize(
        pkg_resources.read_text(interaction, "interaction_model.json"),
        InteractionModelData)

    pot_file_str = "msgid \"\"\n" \
                   "msgstr \"\"\n" \
                   "\n"

    for intent in INTERACTION_MODEL.interaction_model.language_model.intents:
        if intent.samples is not None:
            for sample in intent.samples:
                pot_file_str += f"#: {intent.name}\n" \
                                f"msgid \"{sample.encode('unicode_escape').decode('utf-8')}\"\n" \
                                f"msgstr \"\"\n\n"

    return pot_file_str


def internationalize_interaction_model(interaction_model: InteractionModelData) -> Dict[InteractionModelData]:
    interaction_models = {}
    translations = {}

    locales_path = Path(package_root).parent / "locales"

    for language in SUPPORTED_LANGUAGES:
        translations[language] = gettext.translation("interaction_model",
                                                     localedir=locales_path,
                                                     languages=(language.replace("-", "_"),))

    for lang in SUPPORTED_LANGUAGES:
        translation = translations.get(lang, DEFAULT_LANGUAGE)

        # deep copy the template
        lang_interaction_model = deepcopy(interaction_model)

        for intent in lang_interaction_model.interaction_model.language_model.intents:
            if intent.samples is not None:
                translated_samples = []
                for sample in intent.samples:
                    translated_samples.append(translation.gettext(sample))
                intent.samples = translated_samples

        interaction_models[lang] = lang_interaction_model

    return interaction_models
