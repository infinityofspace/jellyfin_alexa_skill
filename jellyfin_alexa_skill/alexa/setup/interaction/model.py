import importlib.resources as pkg_resources

from ask_sdk_core.serialize import DefaultSerializer
from ask_smapi_model.v1.skill.interaction_model import InteractionModelData

from jellyfin_alexa_skill.alexa.setup import interaction
from jellyfin_alexa_skill.alexa.setup.interaction.l10n import internationalize_interaction_model

INTERACTION_MODEL = DefaultSerializer().deserialize(
    pkg_resources.read_text(interaction, "interaction_model.json"),
    InteractionModelData)

INTERACTION_MODELS = internationalize_interaction_model(INTERACTION_MODEL)
