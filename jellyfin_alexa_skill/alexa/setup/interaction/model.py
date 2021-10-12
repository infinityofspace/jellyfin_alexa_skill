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
