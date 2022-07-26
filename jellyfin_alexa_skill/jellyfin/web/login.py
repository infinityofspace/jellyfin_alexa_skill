import binascii
import logging
import os
import urllib.parse
from pathlib import Path

from flask import Blueprint, request, render_template, redirect, abort
from requests import HTTPError

from jellyfin_alexa_skill.config import VALID_ALEXA_REDIRECT_URLS_REGEX
from jellyfin_alexa_skill.database.model.user import User
from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient

templates_path = Path(__file__).parent.resolve() / "templates"


def get_jellyfin_login_blueprint(jellyfin_server_endpoint: str, client_id: str):
    login_blueprint = Blueprint("login", __name__, template_folder=str(templates_path))

    @login_blueprint.route("/login", methods=["GET"])
    def login_get():
        if client_id != request.args.get("client_id", None):
            return abort(401)

        redirect_uri = request.args.get("redirect_uri", None)
        if not redirect_uri or not VALID_ALEXA_REDIRECT_URLS_REGEX.match(redirect_uri):
            return abort(400)

        state = request.args.get("state", None)
        if not state:
            return abort(400)

        return render_template("login.html",
                               redirect_uri=redirect_uri,
                               client_id=client_id,
                               state=state)

    @login_blueprint.route("/login", methods=["POST"])
    def login_post():
        if client_id != request.form.get("client_id", None):
            return abort(401)

        redirect_uri = request.form.get("redirect_uri", None)
        if not redirect_uri or not VALID_ALEXA_REDIRECT_URLS_REGEX.match(redirect_uri):
            return abort(400)

        state = request.form.get("state", None)
        if not state:
            return abort(400)

        client = JellyfinClient(jellyfin_server_endpoint)

        try:
            user_id, token = client.get_auth_token(username=request.form["username"],
                                                   password=request.form["password"])
        except HTTPError as e:
            if e.response.status_code == 401:
                return render_template("login.html",
                                       redirect_uri=redirect_uri,
                                       state=state,
                                       client_id=client_id,
                                       error="Invalid username or password")
            else:
                return render_template("login.html",
                                       redirect_uri=redirect_uri,
                                       state=state,
                                       client_id=client_id,
                                       error="Something went wrong while accessing your Jellyfin server")
        except ConnectionError as e:
            return render_template("login.html",
                                   redirect_uri=redirect_uri,
                                   state=state,
                                   client_id=client_id,
                                   error="Cant reach your Jellyfin server. Please check your firewall "
                                         "and allow external access to your Jellyfin server")
        except Exception as e:
            logging.error(e)
            return abort(500)

        alexa_auth_token = binascii.hexlify(os.urandom(64)).decode("utf8")

        user = User.create(alexa_auth_token=alexa_auth_token,
                           jellyfin_user_id=user_id,
                           jellyfin_token=token)
        user.save()

        params = {
            "access_token": alexa_auth_token,
            "state": state,
            "token_type": "token"
        }

        return redirect(redirect_uri + "#" + urllib.parse.urlencode(params),
                        code=302)

    return login_blueprint
