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


# update SKILL_MANIFEST's display name and example phrases with "new_name" for the "locale" language
def update_display_name(locale:str, new_name:str):
    default_name = SKILL_MANIFEST.manifest.publishing_information.locales[locale].name

    SKILL_MANIFEST.manifest.publishing_information.locales[locale].name = new_name

    idx = 0
    for phrase in SKILL_MANIFEST.manifest.publishing_information.locales[locale].example_phrases:
        SKILL_MANIFEST.manifest.publishing_information.locales[locale].example_phrases[idx] = phrase.replace(default_name,new_name)
        idx += 1

    return
