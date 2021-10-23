from flask import Blueprint
from flask_ask_sdk.skill_adapter import SkillAdapter


def get_skill_blueprint(skill_adapter: SkillAdapter):
    skill_blueprint = Blueprint("skill", __name__)

    @skill_blueprint.route("/", methods=["POST"])
    def invoke_skill():
        return skill_adapter.dispatch_request()

    return skill_blueprint
