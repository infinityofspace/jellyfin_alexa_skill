# Jellyfin Alexa Skill

Selfhosted Alexa media player skill for Jellyfin

---

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/jellyfin_alexa_skill?style=for-the-badge) ![GitHub](https://img.shields.io/github/license/infinityofspace/jellyfin_alexa_skill?style=for-the-badge)

![PyPI](https://img.shields.io/pypi/v/jellyfin_alexa_skill?style=for-the-badge) ![PyPI - Downloads](https://img.shields.io/pypi/dm/jellyfin_alexa_skill?style=for-the-badge) ![GitHub Workflow Status](https://img.shields.io/github/workflow/status/infinityofspace/jellyfin_alexa_skill/pypi%20release?style=for-the-badge)

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/infinityofspace/jellyfin_alexa_skill/docker%20release?label=Docker&style=for-the-badge)

---

_Note: This project is still in a very early alpha phase, this means not all features are fully functional yet and
features or usage can change significantly between releases. Moreover, new releases can result in data loss of the skill
database. Support for playing videos is currently not fully implemented and may lead to unexpected errors._

### Table of Contents

1. [About](#about)
2. [Features](#features)
3. [Installation](#installation)
4. [Supported languages](#supported-languages)
5. [Skill speech examples](#skill-speech-examples)
6. [Project plan](#project-plan)
7. [FAQ](#faq)
8. [Third party notices](#third-party-notices)
9. [License](#license)

## About

This is a self-hosting Alexa skill to play media from your Jellyfin server. Besides simple playback, other additional
functions like playback of playlists or managing favorites are included. The skill and the Jellyfin player can be used
behind a NAT or firewall without port opening/forwarding. Since the skill and also the Jellyfin server must be reachable
from the outside, in this case the two services are exposed with a tunnel.

## Features

- playback control:
    - play a specific media
    - play media from an artist
    - pause/resume/stop/cancel a playback
    - play previous/next song in queue
    - repeat a single media
    - repeat all media in queue
    - shuffle mode
- playlist:
    - play a specific playlist
- favorite:
    - play favorite media
    - mark current media as favorite
    - remove current media from favorites
- metadata:
    - show the metadata of the media (title and artist)

If you have a feature idea, use
this [issue template](https://github.com/infinityofspace/jellyfin_alexa_skill/issues/new?labels=feature&template=feature_request.md)
to suggest your idea for implementation.

## Installation

Before you begin, make sure you meet the following requirements:

- up-to-date Jellyfin Server with public or local access
- free Amazon developer account
- python 3.6+ or docker + docker-compose installed
- optional:
    - free ngrok account if you're running a local access server

The initial setup requires several steps:

1. create a Alexa skill:
    1. go to the [Amazon Developer Console webpage](https://developer.amazon.com/alexa/console/ask) for Alexa and create
       a new skill
    2. now fill out the skill setup settings:
        1. the skill name can be custom, there are no requirements
        2. choose one of the [supported languages of this skill](#supported-languages) for the `Primary locale`
        3. choose `Custom` for the model type
        4. choose `Provision your own` for the skill's backend resources
        5. on the next page choose `Start from Scratch`
2. generate SMAPI tokens:
    1. create a new security profile for the SMAPI access
       described [here](https://developer.amazon.com/en-US/docs/alexa/smapi/get-access-token-smapi.html#configure-lwa-security-profile)
       to get a `CLIENT-ID` and `CLIENT-SECRET`
    2. install npm if you have not already installed it and install the ask-cli package: `npm install ask-cli -g`
    4. now setup the ask cli: `ask configure`
    5. use the client id and client secret from step i. to generate the refresh
       token: `ask util generate-lwa-tokens --client-id <CLIENT-ID> --client-confirmation <CLIENT-SECRET>`

_Note: The Skill id is needed for the interaction with the Alexa Skill. The SMAPI access is needed for the automatic
setup of the skill._

Use this [config file](skill.conf) and adjust the values which are commented as `required` in the config file. Save the
file in a safe place, because the file contains sensitive credentials. Also remember the save path, because the config
file will be used again later.

Now you are ready to perform the actual installation and startup, you have two options to use the project:

1. use docker:
    - you can build the image locally or use the prebuild images
      on [Github container registry](ghcr.io/infinityofspace/jellyfin_alexa_skill)
        - if you want to build the Docker image locally, use this commands:
          ```commandline
          git clone https://github.com/infinityofspace/jellyfin_alexa_skill
          cd jellyfin_alexa_skill
          docker build -t jellyfin_alexa_skill:latest .
          ```
    - start the skill:
      ```commandline
      docker run \
      -v /path/to/the/skill.conf:/var/lib/jellyfin_alexa_skill/config/skill.conf \
      -v /path/to/persistence/skill/data:/var/lib/jellyfin_alexa_skill/data \
      ghcr.io/infinityofspace/jellyfin_alexa_skill:latest
      ```

OR

2. with pip:
    - install:
        - from pypi:`pip3 install jellyfin_alexa_skill`
        - you can also install from source:
          ```commandline
          git clone https://github.com/infinityofspace/jellyfin_alexa_skill
          cd jellyfin_alexa_skill
          pip3 install .
          ```
    - start the skill: `jellyfin_alexa_skill --config /path/to/skill.conf --data /path/to/skill/data/`

_Note: The default path for the skill.conf file is `/home/user/.jellyfin_alexa_skill/config/skill.conf` and for the
skill data path it is `/home/user/.jellyfin_alexa_skill/data`._ You can adjust the paths with the `config` and `data` or
as environment variables `JELLYFIN_ALEXA_SKILL_CONFIG` and `JELLYFIN_ALEXA_SKILL_DATA`.

Now activate the skill in your Alexa app, then you can use the skill with your Alexa enabled devices.

## Supported languages

The skill has support for the following languages:

- English
- German (currently only english Alexa response)

## Skill speech examples

The [wiki](https://github.com/infinityofspace/jellyfin_alexa_skill/wiki/Interaction-examples) contains examples how to
interact with the skill.

## Project plan

Take a look at the [project plan](https://github.com/infinityofspace/jellyfin_alexa_skill/projects) to see what features
and bug fixes are planned and in progress.

## FAQ

You can find the FAQ [here](https://github.com/infinityofspace/jellyfin_alexa_skill/wiki/FAQ).

## Third party notices

| Module | License | Project |
|:------:|:------:|:------:|
| flask-ask-sdk | [License](https://raw.githubusercontent.com/alexa/alexa-skills-kit-sdk-for-python/master/LICENSE) | [Project](https://github.com/alexa/alexa-skills-kit-sdk-for-python) |
| jellyfin-apiclient-python | [License](https://raw.githubusercontent.com/jellyfin/jellyfin-apiclient-python/master/LICENSE.md) | [Project](https://github.com/jellyfin/jellyfin-apiclient-python) |
| pyngrok | [License](https://raw.githubusercontent.com/alexdlaird/pyngrok/main/LICENSE) | [Project](https://github.com/alexdlaird/pyngrok) |
| ask-smapi-sdk | [License](https://raw.githubusercontent.com/alexa/alexa-skills-kit-sdk-for-python/master/LICENSE) | [Project](https://github.com/alexa/alexa-skills-kit-sdk-for-python) |
| ask-smapi-model | [License](https://raw.githubusercontent.com/alexa/alexa-apis-for-python/master/LICENSE) | [Project](https://github.com/alexa/alexa-apis-for-python) |
| rapidfuzz | [License](https://raw.githubusercontent.com/maxbachmann/RapidFuzz/main/LICENSE) | [Project](https://github.com/maxbachmann/RapidFuzz) |
| peewee | [License](https://raw.githubusercontent.com/coleifer/peewee/master/LICENSE) | [Project](https://github.com/coleifer/peewee) |
| gunicorn | [License](https://raw.githubusercontent.com/benoitc/gunicorn/master/LICENSE) | [Project](https://github.com/benoitc/gunicorn) |

Furthermore, this readme file contains embeddings of [Shields.io](https://github.com/badges/shields).

## License

[GPL-3.0](https://github.com/infinityofspace/jellyfin_alexa_skill/blob/main/LICENSE)
