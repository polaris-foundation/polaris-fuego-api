import base64
from typing import Any

from environs import Env
from flask import Flask


def get_value_or_none(var: Any) -> Any:
    return var if var != "None" else None


class Configuration:
    env = Env()

    # required
    FHIR_SERVER_BASE_URL = env.str("FHIR_SERVER_BASE_URL")
    FHIR_SERVER_MRN_SYSTEM = env.str("FHIR_SERVER_MRN_SYSTEM", "MRN")

    # optional
    FHIR_SERVER_AUTH_METHOD = get_value_or_none(
        env.str("FHIR_SERVER_AUTH_METHOD", "None")
    )
    FHIR_SERVER_TOKEN_URL = get_value_or_none(env.str("FHIR_SERVER_TOKEN_URL", "None"))
    FHIR_SERVER_TOKEN_PRIVATE_KEY = get_value_or_none(
        env.str("FHIR_SERVER_TOKEN_PRIVATE_KEY", "None")
    )
    FHIR_SERVER_CLIENT_ID = get_value_or_none(env.str("FHIR_SERVER_CLIENT_ID", "None"))
    FHIR_SERVER_CLIENT_SECRET = get_value_or_none(
        env.str("FHIR_SERVER_CLIENT_SECRET", "None")
    )

    if FHIR_SERVER_TOKEN_PRIVATE_KEY:
        FHIR_SERVER_TOKEN_PRIVATE_KEY = base64.b64decode(
            FHIR_SERVER_TOKEN_PRIVATE_KEY
        ).decode("UTF-8")


def init_config(app: Flask) -> None:
    app.config.from_object(fuego_config)


fuego_config = Configuration()
