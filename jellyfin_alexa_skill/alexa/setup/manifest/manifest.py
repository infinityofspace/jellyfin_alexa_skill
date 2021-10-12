import importlib.resources as pkg_resources

from ask_sdk_core.serialize import DefaultSerializer
from ask_smapi_model.services.skill_management import SkillManagementServiceClient
from ask_smapi_model.v1.skill.manifest import SkillManifestEnvelope

from jellyfin_alexa_skill.alexa.setup import manifest as manifest_module

BASE_NAME = "jellyfin"

SKILL_MANIFEST = DefaultSerializer().deserialize(pkg_resources.read_text(manifest_module, "manifest.json"),
                                                 SkillManifestEnvelope)


def get_skill_version(manifest: SkillManifestEnvelope) -> str:
    name = manifest.manifest.publishing_information.name
    if not name:
        name = ""
    skill_version = name.replace(BASE_NAME + "_", "")
    return skill_version


def update_skill_version(client: SkillManagementServiceClient,
                         version: str,
                         skill_id: str,
                         stage: str = "development") -> None:
    manifest = client.get_skill_manifest_v1(skill_id=skill_id,
                                            stage_v2=stage)

    name = "_".join([BASE_NAME, version])
    manifest.manifest.publishing_information.name = name

    client.update_skill_manifest_v1(skill_id=skill_id,
                                    stage_v2=stage,
                                    update_skill_request=manifest)
