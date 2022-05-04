import importlib.resources as pkg_resources

from ask_sdk_core.serialize import DefaultSerializer
from ask_smapi_model.v1.skill.interaction_model import InteractionModelData

from jellyfin_alexa_skill.alexa.setup import interaction

INTERACTION_MODEL_EN_US = DefaultSerializer().deserialize(
    pkg_resources.read_text(interaction, "interaction_model_en_US.json"),
    InteractionModelData)

INTERACTION_MODEL_DE_DE = DefaultSerializer().deserialize(
    pkg_resources.read_text(interaction, "interaction_model_de_DE.json"),
    InteractionModelData)

INTERACTION_MODEL_IT_IT = DefaultSerializer().deserialize(
    pkg_resources.read_text(interaction, "interaction_model_it_IT.json"),
    InteractionModelData)

INTERACTION_MODEL_ES_ES = DefaultSerializer().deserialize(
    pkg_resources.read_text(interaction, "interaction_model_es_ES.json"),
    InteractionModelData)

INTERACTION_MODELS = {
    "en-US": INTERACTION_MODEL_EN_US,
    "de-DE": INTERACTION_MODEL_DE_DE,
    "it-IT": INTERACTION_MODEL_IT_IT,
    "es-ES": INTERACTION_MODEL_ES_ES,
}
