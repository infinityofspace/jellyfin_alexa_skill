from babel.messages.frontend import compile_catalog, extract_messages, init_catalog, update_catalog
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py

from jellyfin_alexa_skill import __version__

with open("Readme.md") as f:
    long_description = f.read()

install_requires = [
    "flask-ask-sdk~=1.0.0",
    "pyngrok~=5.1.0",
    "ask-smapi-sdk~=1.0.0",
    "ask_smapi_model~=1.13.1",
    "peewee~=3.14.4",
    "gunicorn~=20.1.0",
    "Flask-WTF~=0.15.1"
]

setup_requires = [
    "Babel~=2.9.1",
]


class CompileCatalogAndBuildPyCommand(build_py):
    def run(self):
        self.run_command("compile_catalog")
        build_py.run(self)


class CompileCatalogCommand(compile_catalog):
    def initialize_options(self):
        compile_catalog.initialize_options(self)
        self.directory = "jellyfin_alexa_skill/locales"
        self.domain = "skill"
        self.use_fuzzy = True


class ExtractMessagesCommand(extract_messages):
    def initialize_options(self):
        extract_messages.initialize_options(self)
        self.omit_header = True
        self.input_dirs = "jellyfin_alexa_skill"
        self.output_file = "jellyfin_alexa_skill/locales/base.pot"


class UpdateCatalogCommand(update_catalog):
    def initialize_options(self):
        update_catalog.initialize_options(self)
        self.omit_header = True
        self.output_dir = "jellyfin_alexa_skill/locales"
        self.domain = "skill"
        self.input_file = "jellyfin_alexa_skill/locales/base.pot"


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
    python_requires=">=3.6",
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
            "jellyfin_alexa_skill = jellyfin_alexa_skill.main:main",
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
