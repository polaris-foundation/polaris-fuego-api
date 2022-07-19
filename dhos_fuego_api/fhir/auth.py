import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import requests
from jose import jwt as jose_jwt
from requests import PreparedRequest
from requests.auth import HTTPBasicAuth
from she_logging import logger

from dhos_fuego_api.config import fuego_config
from dhos_fuego_api.fhir.error_handler import (
    FhirException,
    FhirServerUnavailableException,
)


class AuthDispatcher:
    auth_method: Optional[str] = fuego_config.FHIR_SERVER_AUTH_METHOD

    token: Optional[str] = None
    expiry: Optional[datetime] = None
    lock: threading.Lock = threading.Lock()

    @staticmethod
    def auth(r: PreparedRequest) -> PreparedRequest:
        """
        Append authorization headers to the request. To be used only as a
            request library `auth` argument.
        @param r: requests.PreparedRequest object
        @return: requests.PreparedRequest object
        """
        if AuthDispatcher.auth_method is None:
            pass
        elif AuthDispatcher.auth_method == "basic":
            AuthDispatcher.get_basic_auth()(r)
        elif AuthDispatcher.auth_method.startswith("token"):
            r.headers["Authorization"] = f"Bearer {AuthDispatcher.get_token()}"
        else:
            raise FhirException(
                f"Unsupported token auth method: {AuthDispatcher.auth_method}"
            )
        return r

    @staticmethod
    def clear() -> None:
        AuthDispatcher.token = None
        AuthDispatcher.expiry = None

    @staticmethod
    def expired() -> bool:
        if (
            AuthDispatcher.token is None
            or AuthDispatcher.expiry is None
            or AuthDispatcher.expiry < datetime.now()
        ):
            return True
        return False

    @staticmethod
    def get_token() -> str:
        with AuthDispatcher.lock:
            if AuthDispatcher.expired():
                (
                    AuthDispatcher.token,
                    AuthDispatcher.expiry,
                ) = AuthDispatcher.fetch_token()

            # https://github.com/python/mypy/issues/7105
            return AuthDispatcher.token  # type: ignore

    @staticmethod
    def get_basic_auth() -> HTTPBasicAuth:
        return HTTPBasicAuth(
            username=fuego_config.FHIR_SERVER_CLIENT_ID,
            password=fuego_config.FHIR_SERVER_CLIENT_SECRET,
        )

    @staticmethod
    def fetch_token() -> Tuple[str, datetime]:
        """
        There are different kinds of auth methods to retrieve a token
            depending on a provider

        @return: token as a string and expiry datetime as a datetime
        """
        if AuthDispatcher.auth_method == "token_basic":
            return AuthDispatcher._fetch_token_basic()
        elif AuthDispatcher.auth_method == "token_epic":
            return AuthDispatcher._fetch_token_epic()
        else:
            raise FhirException(
                f"Unsupported token auth method: {AuthDispatcher.auth_method}"
            )

    @staticmethod
    def _fetch_token_basic() -> Tuple[str, datetime]:
        access_key_auth: HTTPBasicAuth = HTTPBasicAuth(
            fuego_config.FHIR_SERVER_CLIENT_ID,
            fuego_config.FHIR_SERVER_CLIENT_SECRET,
        )
        try:
            token_response = requests.post(
                fuego_config.FHIR_SERVER_TOKEN_URL,
                auth=access_key_auth,
                data={"grant_type": "client_credentials", "scope": ""},
            )
            token_response.raise_for_status()
        except requests.HTTPError as e:
            logger.exception(
                "Unexpected response from auth server: HTTP %s",
                e.response.status_code,
                extra={"response_body": e.response.text},
            )
            raise FhirException(
                f"Unexpected response from the auth server: {e.response.status_code} {e.response.text}"
            )
        except requests.RequestException:
            raise FhirServerUnavailableException("Could not connect to the auth server")

        token_response_json = token_response.json()
        logger.debug("Received response: %s", token_response_json)
        token: str = token_response_json.get("access_token")
        expiry_seconds = token_response_json.get("expires_in", 3600)
        expiry: datetime = datetime.now() + timedelta(seconds=int(expiry_seconds))

        return token, expiry

    @staticmethod
    def _fetch_token_epic() -> Tuple[str, datetime]:
        # https://fhir.epic.com/Documentation?docId=oauth2&section=BackendOAuth2Guide

        # construct jwt
        jwt_claims = {
            "alg": "RS384",
            "typ": "JWT",
            "aud": fuego_config.FHIR_SERVER_TOKEN_URL,
            "iss": fuego_config.FHIR_SERVER_CLIENT_ID,
            "sub": fuego_config.FHIR_SERVER_CLIENT_ID,
            "jti": str(uuid.uuid4()),
            "exp": (datetime.now() + timedelta(minutes=5)).timestamp(),
        }

        try:
            encoded_jwt = jose_jwt.encode(
                claims=jwt_claims,
                key=fuego_config.FHIR_SERVER_TOKEN_PRIVATE_KEY,
                algorithm=jose_jwt.ALGORITHMS.RS384,
            )
        except jose_jwt.JWTError as e:
            raise FhirException(f"Cannot encode the JWT claims: {e}")

        request_body: Dict = {
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": encoded_jwt,
        }

        # get token
        try:
            response = requests.post(
                url=fuego_config.FHIR_SERVER_TOKEN_URL,
                data=request_body,
            )
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.exception(
                "Unexpected response from auth server: HTTP %s",
                e.response.status_code,
                extra={"response_body": e.response.text},
            )
            raise FhirException(
                f"Unexpected response from the auth server: {e.response.status_code} {e.response.text}"
            )
        except requests.RequestException:
            raise FhirServerUnavailableException("Could not connect to the auth server")

        response_json: Dict = response.json()
        access_token: str = response_json["access_token"]
        expires_in: int = int(response_json.get("expires_in", 3600))
        return access_token, datetime.now() + timedelta(seconds=expires_in)
