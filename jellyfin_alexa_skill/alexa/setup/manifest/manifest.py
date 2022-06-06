import importlib.resources as pkg_resources

from ask_sdk_core.serialize import DefaultSerializer
from ask_smapi_model.v1.skill.manifest import SkillManifestEnvelope

from jellyfin_alexa_skill import __version__
from jellyfin_alexa_skill.alexa.setup import manifest as manifest_module
from jellyfin_alexa_skill.alexa.setup.manifest.l10n import internationalize_manifest

BASE_NAME = "jellyfin"

manifest = DefaultSerializer().deserialize(pkg_resources.read_text(manifest_module, "manifest.json"),
                                           SkillManifestEnvelope)
manifest.manifest.publishing_information.name = manifest.manifest.publishing_information.name + "_" + __version__

SKILL_MANIFEST = internationalize_manifest(manifest)


def get_skill_version(manifest: SkillManifestEnvelope) -> str:
    name = manifest.manifest.publishing_information.name
    if not name:
        name = ""
    skill_version = name.replace(BASE_NAME + "_", "")
    return skill_version
