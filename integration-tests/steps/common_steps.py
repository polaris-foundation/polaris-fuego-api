from behave import given
from behave.runner import Context
from helpers.jwt import get_system_token


@given("a valid JWT")
def get_system_jwt(context: Context) -> None:
    if not hasattr(context, "system_jwt"):
        context.system_jwt = get_system_token()
