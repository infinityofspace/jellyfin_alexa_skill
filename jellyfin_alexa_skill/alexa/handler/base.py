from abc import abstractmethod, ABC
from functools import wraps

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.ui.link_account_card import LinkAccountCard
from peewee import DoesNotExist

from jellyfin_alexa_skill.database.model.user import User
from jellyfin_alexa_skill.l10n import get_translation


class BaseHandler(AbstractRequestHandler, ABC):
    def handle(self, handler_input: HandlerInput, *args, **kwargs):
        alexa_auth_token = handler_input.request_envelope.context.system.user.access_token

        if not alexa_auth_token:
            handler_input.response_builder.set_card(LinkAccountCard())
            return handler_input.response_builder.response

        try:
            user = User.get(alexa_auth_token=alexa_auth_token)
        except DoesNotExist:
            handler_input.response_builder.set_card(LinkAccountCard())
            return handler_input.response_builder.response

        return self.handle_func(user=user, handler_input=handler_input, *args, **kwargs)

    @abstractmethod
    def handle_func(self, user: User, handler_input: HandlerInput, *args, **kwargs):
        pass

    @staticmethod
    def translate(func):
        @wraps(func)
        def wrapper(self, handler_input: HandlerInput, *args, **kwargs):
            translation = get_translation(handler_input.request_envelope.request.locale)

            return func(self, handler_input=handler_input, translation=translation, *args, **kwargs)

        return wrapper
