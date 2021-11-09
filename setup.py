from setuptools import setup, find_packages

from jellyfin_alexa_skill import __version__

with open("Readme.md") as f:
    long_description = f.read()

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
    install_requires=[
        "flask-ask-sdk~=1.0.0",
        "pyngrok~=5.1.0",
        "ask-smapi-sdk~=1.0.0",
        "ask_smapi_model~=1.13.1",
        "peewee~=3.14.4",
        "gunicorn~=20.1.0",
        "Flask-WTF~=0.15.1"
    ],
    setup_requires=[
        "Babel~=2.9.1",
    ],
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
    }
)
