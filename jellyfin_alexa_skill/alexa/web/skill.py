from flask import Blueprint
from flask_ask_sdk.skill_adapter import SkillAdapter


def get_skill_blueprint(skill_adapter: SkillAdapter):
    skill_blueprint = Blueprint("skill", __name__)

    @skill_blueprint.route("/", methods=["POST"])
    def invoke_skill():
        return skill_adapter.dispatch_request()

    @skill_blueprint.route("/healthy", methods=["GET"])
    def health_check():
        """
        The docker-compose HEALTHCHECK relies on the alexa skill server sending a response for "/healthy".
        We could send anything in response, but "OK" is sufficient.

        As an added bonus, you can check that your Alexa skill server is up with: https://my.alexa.server/healthy

        note: for GET, Flask automatically adds support for HEAD method
              see: https://flask.palletsprojects.com/en/2.0.x/quickstart/#a-minimal-application ("HTTP Methods")
        """
        return "OK"

    return skill_blueprint
