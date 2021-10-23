import argparse
import binascii
import logging
import os
import textwrap
import time
import uuid
from pathlib import Path

import ask_sdk_model_runtime
from ask_smapi_model.v1.skill.account_linking import AccountLinkingRequest, AccountLinkingRequestPayload, \
    AccountLinkingType
from ask_smapi_model.v1.skill.manifest import SSLCertificateType, SkillManifestEndpoint
from ask_smapi_sdk import StandardSmapiClientBuilder
from flask import Flask
from flask_ask_sdk.skill_adapter import SkillAdapter
from flask_wtf import CSRFProtect
from gunicorn.app.base import BaseApplication
from pyngrok import conf, ngrok

from jellyfin_alexa_skill import __version__
from jellyfin_alexa_skill.alexa.handler import get_skill_builder
from jellyfin_alexa_skill.alexa.setup.interaction.model import INTERACTION_MODEL_DE_DE, INTERACTION_MODEL_EN_US
from jellyfin_alexa_skill.alexa.setup.manifest.manifest import get_skill_version, SKILL_MANIFEST
from jellyfin_alexa_skill.alexa.web.skill import get_skill_blueprint
from jellyfin_alexa_skill.config import get_config, DEFAULT_ALEXA_SKILL_CONFIG_PATH, DEFAULT_ALEXA_SKILL_DATA_PATH, \
    APP_NAME
from jellyfin_alexa_skill.database.db import connect_db
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient
from jellyfin_alexa_skill.jellyfin.web.login import get_jellyfin_login_blueprint

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)


class GunicornApplication(BaseApplication):

    def init(self, parser, opts, args):
        pass

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        conf = {key: value for key, value in self.options.items()
                if key in self.cfg.settings and value is not None}
        for key, value in conf.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    parser = argparse.ArgumentParser(
        description="Selfhosted Alexa media player skill for Jellyfin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
                                    License:
                                        GPL-3.0
                                    Source:
                                        https://github.com/infinityofspace/jellyfin_alexa_skill
                                """)
    )

    parser.add_argument("--config", help="Path to the config file", required=False)
    parser.add_argument("--data", help="Path to the data folder", required=False)

    args = parser.parse_args()

    # program arguments take precedence over environment variables
    if args.config:
        config_path = Path(args.config)
    else:
        config_path = Path(
            os.environ.get("JELLYFIN_ALEXA_SKILL_CONFIG", DEFAULT_ALEXA_SKILL_CONFIG_PATH))

    if args.data:
        data_path = Path(args.data)
    else:
        data_path = Path(os.environ.get("JELLYFIN_ALEXA_SKILL_DATA", DEFAULT_ALEXA_SKILL_DATA_PATH))

    if not config_path.exists():
        raise FileNotFoundError(f"Config file {config_path} not found")

    config = get_config(config_path)

    if "data" not in config:
        config["data"] = {}
        with open(str(config_path), "w") as f:
            config.write(f)

    app = Flask(__name__)

    flask_secret = config["data"].get("flask_secret", None)

    if not flask_secret:
        flask_secret = binascii.hexlify(os.urandom(32)).decode("utf8")
        config["data"]["flask_secret"] = flask_secret
        with open(str(config_path), "w") as f:
            config.write(f)

    app.secret_key = flask_secret

    csrf = CSRFProtect(app)

    skill_endpoint = config["general"]["skill_endpoint"]
    jellyfin_endpoint = config["general"]["jellyfin_endpoint"]

    host = "0.0.0.0"

    if not skill_endpoint or not jellyfin_endpoint:
        ngrok_auth_token = config["ngrok"]["auth_token"]
        if ngrok_auth_token is None or len(ngrok_auth_token) == 0:
            raise Exception("No ngrok auth token. Please add your auth token to the skill.conf file.")

        pyngrok_config = conf.PyngrokConfig(auth_token=ngrok_auth_token,
                                            region=config["ngrok"].get("region", "us"))

        if not skill_endpoint:
            skill_ngrok_connection = ngrok.connect(pyngrok_config=pyngrok_config,
                                                   addr=config["general"]["web_app_port"],
                                                   name="jellyfin_alexa_skill",
                                                   bind_tls=True)
            logging.info("ngrok tunnel for skill: " + str(skill_ngrok_connection))
            skill_endpoint = skill_ngrok_connection.public_url
            # we don't need to bind for external access when using a tunnel
            host = "127.0.0.1"

        jellyfin_addr = config["ngrok"]["jellyfin_addr"]
        if jellyfin_addr:
            jellyfin_ngrok_connection = ngrok.connect(pyngrok_config=pyngrok_config,
                                                      addr=jellyfin_addr,
                                                      name="jellyfin_server",
                                                      bind_tls=True)
            logging.info("ngrok tunnel for jellyfin: " + str(jellyfin_ngrok_connection))
            jellyfin_endpoint = jellyfin_ngrok_connection.public_url

    smapi_client_builder = StandardSmapiClientBuilder(
        client_id=config["smapi"]["client_id"],
        client_secret=config["smapi"]["client_secret"],
        refresh_token=config["smapi"]["refresh_token"])
    smapi_client = smapi_client_builder.client()

    skill_id = config["general"]["skill_id"]
    stage = "development"

    manifest = smapi_client.get_skill_manifest_v1(skill_id=skill_id, stage_v2=stage)

    skill_version = get_skill_version(manifest)

    # update the skill in the could when we are on an older version or force reset to clean manual changes
    if config["general"].getboolean("force_reset_skill") or skill_version != __version__:
        logging.info("Updating skill interaction model...")

        smapi_client.set_interaction_model_v1(skill_id=skill_id,
                                              stage_v2=stage,
                                              locale="en_US",
                                              interaction_model=INTERACTION_MODEL_EN_US)

        smapi_client.set_interaction_model_v1(skill_id=skill_id,
                                              stage_v2=stage,
                                              locale="de_DE",
                                              interaction_model=INTERACTION_MODEL_DE_DE)

        # wait a few seconds to let the changed build
        wait_time = 30
        logging.info(f"Wait {wait_time} seconds for the interactions model to be build in the cloud")
        time.sleep(wait_time)
        logging.info("Skill interaction model updated")

    ssl_cert_type_str = config["general"]["skill_endpoint_ssl_cert_type"]
    if ssl_cert_type_str == "wildcard" or skill_endpoint[-9:] == ".ngrok.io":
        # when using ngrok endpoints the ssl cert is always a wildcard cert
        ssl_cert_type = SSLCertificateType.Wildcard
    elif ssl_cert_type_str == "trusted":
        ssl_cert_type = SSLCertificateType.Trusted
    elif ssl_cert_type_str == "self_signed":
        ssl_cert_type = SSLCertificateType.SelfSigned
    else:
        raise Exception("Invalid ssl certificate type defined")

    # check if the current saved endpoint or ssl cert type requires an update
    if config["general"].getboolean("force_reset_skill") \
            or skill_version != __version__ \
            or manifest.manifest.apis.custom.endpoint is None \
            or manifest.manifest.apis.custom.endpoint.uri != skill_endpoint \
            or manifest.manifest.apis.custom.endpoint.ssl_certificate_type != ssl_cert_type:
        logging.info("Updating skill endpoint...")

        manifest = SKILL_MANIFEST

        manifest.manifest.apis.custom.endpoint = SkillManifestEndpoint(skill_endpoint,
                                                                       ssl_certificate_type=ssl_cert_type)

        smapi_client.update_skill_manifest_v1(skill_id=skill_id,
                                              stage_v2=stage,
                                              update_skill_request=manifest)

        logging.info("Skill endpoint updated")

    if "data" not in config:
        config["data"] = {}
        with open(str(config_path), "w") as f:
            config.write(f)

    account_linking_client_id = config["data"].get("alexa_account_linking_client_id", None)
    if not account_linking_client_id:
        account_linking_client_id = str(uuid.uuid4())
        config["data"]["alexa_account_linking_client_id"] = account_linking_client_id
        with open(str(config_path), "w") as f:
            config.write(f)

    account_linking_url = skill_endpoint + "/login"

    try:
        account_linking_info = smapi_client.get_account_linking_info_v1(skill_id=skill_id,
                                                                        stage_v2=stage).accountLinkingResponse
    except ask_sdk_model_runtime.exceptions.ServiceException:
        # the account linking is disabled
        account_linking_info = None

    if config["general"].getboolean("force_reset_skill") \
            or skill_version != __version__ \
            or account_linking_info is None \
            or account_linking_info["clientId"] != account_linking_client_id \
            or account_linking_info["authorizationUrl"] != account_linking_url \
            or account_linking_info["type"] != AccountLinkingType.IMPLICIT.value:
        logging.info("Updating account linking settings...")

        account_linking_request = AccountLinkingRequest(
            AccountLinkingRequestPayload(authorization_url=account_linking_url,
                                         client_id=account_linking_client_id,
                                         object_type=AccountLinkingType.IMPLICIT))

        smapi_client.update_account_linking_info_v1(skill_id=skill_id,
                                                    stage_v2=stage,
                                                    account_linking_request=account_linking_request)

        logging.info("account linking settings updated")

    data_path.mkdir(parents=True, exist_ok=True)
    connect_db(data_path / "data.sqlite")

    jellyfin_client = JellyfinClient(server_endpoint=jellyfin_endpoint, client_name=APP_NAME)

    skill_adapter = SkillAdapter(skill=get_skill_builder(jellyfin_client).create(),
                                 skill_id=skill_id,
                                 app=app)

    # register skill routes
    skill_blueprint = get_skill_blueprint(skill_adapter)
    csrf.exempt(skill_blueprint)
    app.register_blueprint(skill_blueprint)

    # register login routes
    login_blueprint = get_jellyfin_login_blueprint(jellyfin_endpoint, account_linking_client_id)
    app.register_blueprint(login_blueprint)

    web_app_port = config["general"]["web_app_port"]

    options = {
        "bind": f"{host}:{web_app_port}",
        "workers": 2,
    }
    GunicornApplication(app, options).run()


if __name__ == "__main__":
    main()
