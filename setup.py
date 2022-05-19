from distutils.cmd import Command
from pathlib import Path

from babel.messages.frontend import compile_catalog, extract_messages, init_catalog, update_catalog
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py

from jellyfin_alexa_skill import __version__
from jellyfin_alexa_skill.alexa.setup.interaction.l10n import build_pot_file_str as interaction_build_pot_file_str
from jellyfin_alexa_skill.alexa.setup.manifest.l10n import build_pot_file_str as manifest_build_pot_file_str

with open("Readme.md") as f:
    long_description = f.read()

install_requires = [
    "flask-ask-sdk~=1.0.0",
    "ask-smapi-sdk~=1.0.0",
    "ask_smapi_model>=1.13.1,<1.15.0",
    "peewee~=3.14.4",
    "gunicorn~=20.1.0",
    "Flask-WTF>=0.15.1,<1.1.0"
]

setup_requires = [
    "Babel>=2.9.1,<2.11.0",
]

LOCAL_BASE_PATH = Path("jellyfin_alexa_skill/locales")


class CompileCatalogAndBuildPyCommand(build_py):
    def run(self):
        self.run_command("compile_catalog")
        build_py.run(self)


class CompileCatalogCommand(compile_catalog):
    def initialize_options(self):
        compile_catalog.initialize_options(self)
        self.directory = "jellyfin_alexa_skill/locales"
        self.domain = "skill manifest interaction_model"
        self.use_fuzzy = True


class ExtractMessagesCommand(Command):
    description = "Extract messages from source code"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # extract skill messages
        cmd = SkillExtractMessagesCommand()
        cmd.initialize_options()
        cmd.finalize_options()
        cmd.run()

        # extract manifest messages
        manifest_pot_file_str = manifest_build_pot_file_str()
        with (LOCAL_BASE_PATH / "manifest.pot").open("w") as f:
            f.write(manifest_pot_file_str)

        # extract interaction model messages
        interaction_model_pot_file_str = interaction_build_pot_file_str()
        with (LOCAL_BASE_PATH / "interaction_model.pot").open("w") as f:
            f.write(interaction_model_pot_file_str)


class SkillExtractMessagesCommand(extract_messages):
    def initialize_options(self):
        extract_messages.initialize_options(self)
        self.input_paths = "jellyfin_alexa_skill"
        self.output_file = "jellyfin_alexa_skill/locales/skill.pot"


class UpdateCatalogCommand(Command):
    description = "Update the message catalogs"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        cmd = UpdateSkillCatalogCommand()
        cmd.initialize_options()
        cmd.finalize_options()
        cmd.run()

        # update manifest catalog
        cmd = UpdateManifestCatalogCommand()
        cmd.initialize_options()
        cmd.finalize_options()
        cmd.run()

        # update interaction model catalog
        cmd = UpdateInteractionModelCatalogCommand()
        cmd.initialize_options()
        cmd.finalize_options()
        cmd.run()


class UpdateSkillCatalogCommand(update_catalog):
    def initialize_options(self):
        update_catalog.initialize_options(self)
        self.output_dir = "jellyfin_alexa_skill/locales"
        self.domain = "skill"
        self.input_file = "jellyfin_alexa_skill/locales/skill.pot"
        self.no_wrap = True
        self.ignore_obsolete = True
        self.update_header_comment = False


class UpdateManifestCatalogCommand(update_catalog):
    def initialize_options(self):
        update_catalog.initialize_options(self)
        self.output_dir = "jellyfin_alexa_skill/locales"
        self.domain = "manifest"
        self.input_file = "jellyfin_alexa_skill/locales/manifest.pot"
        self.no_wrap = True
        self.ignore_obsolete = True
        self.update_header_comment = False


class UpdateInteractionModelCatalogCommand(update_catalog):
    def initialize_options(self):
        update_catalog.initialize_options(self)
        self.output_dir = "jellyfin_alexa_skill/locales"
        self.domain = "interaction_model"
        self.input_file = "jellyfin_alexa_skill/locales/interaction_model.pot"
        self.no_wrap = True
        self.ignore_obsolete = True
        self.update_header_comment = False


setup(
    name="jellyfin_alexa_skill",
    version=__version__,
    author="infinityofspace",
    url="https://github.com/infinityofspace/jellyfin_alexa_skill",
    description="Selfhosted Alexa media player skill for Jellyfin",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Utilities",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Video"
    ],
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=install_requires,
    setup_requires=setup_requires,
    package_data={
        "jellyfin_alexa_skill": [
            "alexa/setup/interaction/*.json",
            "alexa/setup/manifest/*.json",
            "locales/*/*/*.po",
            "locales/*/*/*.mo",
            "jellyfin/web/templates/*.html"
        ]
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "jellyfin-alexa-skill = jellyfin_alexa_skill.main:main",
        ]
    },
    cmdclass={
        "build_py": CompileCatalogAndBuildPyCommand,
        "compile_catalog": CompileCatalogCommand,
        "extract_messages": ExtractMessagesCommand,
        "init_catalog": init_catalog,
        "update_catalog": UpdateCatalogCommand
    }
)
