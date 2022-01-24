import importlib.resources as pkg_resources

from ask_sdk_core.serialize import DefaultSerializer
from ask_smapi_model.v1.skill.manifest import SkillManifestEnvelope

from jellyfin_alexa_skill import __version__
from jellyfin_alexa_skill.alexa.setup import manifest as manifest_module

BASE_NAME = "jellyfin"

_manifest = DefaultSerializer().deserialize(pkg_resources.read_text(manifest_module, "manifest.json"),
                                            SkillManifestEnvelope)
_manifest.manifest.publishing_information.name = _manifest.manifest.publishing_information.name + "_" + __version__

SKILL_MANIFEST = _manifest


def get_skill_version(manifest: SkillManifestEnvelope) -> str:
    name = manifest.manifest.publishing_information.name
    if not name:
        name = ""
    skill_version = name.replace(BASE_NAME + "_", "")
    return skill_version
