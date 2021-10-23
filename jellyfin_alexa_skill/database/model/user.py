from peewee import CharField

from jellyfin_alexa_skill.database.model.base import BaseModel


class User(BaseModel):
    alexa_auth_token = CharField(primary_key=True)
    jellyfin_user_id = CharField()
    jellyfin_token = CharField()

    class Meta:
        table_name = "User"
