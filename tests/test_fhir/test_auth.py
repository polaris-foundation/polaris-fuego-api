from datetime import datetime, timedelta

import pytest
import requests
from environs import Env
from mock import Mock
from pytest_mock import MockFixture
from requests.auth import HTTPBasicAuth
from requests_mock import Mocker

from dhos_fuego_api.fhir import auth
from dhos_fuego_api.fhir.error_handler import (
    FhirException,
    FhirServerUnavailableException,
)


class TestAuth:
    @pytest.fixture(autouse=True)
    def clear_token_cache(self) -> None:
        auth.AuthDispatcher.clear()

    @pytest.fixture
    def mock_jose_jwt_encode(self, mocker: MockFixture) -> Mock:
        return mocker.patch.object(auth.jose_jwt, "encode", return_value="jwt")

    def test_auth_dispatcher_cache(
        self, mock_auth_success: Mock, mock_jose_jwt_encode: Mock
    ) -> None:
        for _ in range(100):
            auth.AuthDispatcher.get_token()
        assert mock_auth_success.call_count == 1

    def test_auth_dispatcher_clear(
        self, mock_jose_jwt_encode: Mock, mock_auth_success: Mock
    ) -> None:
        assert auth.AuthDispatcher.token is None
        assert auth.AuthDispatcher.expiry is None
        auth.AuthDispatcher.get_token()
        assert auth.AuthDispatcher.token is not None
        assert auth.AuthDispatcher.expiry is not None
        auth.AuthDispatcher.clear()
        assert auth.AuthDispatcher.token is None
        assert auth.AuthDispatcher.expiry is None

    def test_auth_dispatcher_expired(self, mock_jose_jwt_encode: Mock) -> None:
        now = datetime.now()
        after_5_seconds = now + timedelta(seconds=5)
        before_5_seconds = now - timedelta(seconds=5)
        auth.AuthDispatcher.token = "TOKEN"
        auth.AuthDispatcher.expiry = after_5_seconds
        assert not auth.AuthDispatcher.expired()
        auth.AuthDispatcher.expiry = before_5_seconds
        assert auth.AuthDispatcher.expired()

    @pytest.mark.parametrize(
        "auth_method", ("basic", "token_basic", "token_epic", None, "abrakadabra")
    )
    def test_auth_dispatcher_auth(
        self, mocker: MockFixture, auth_method: str, mock_jose_jwt_encode: Mock
    ) -> None:
        token: str = "TOKEN"
        basic_auth: HTTPBasicAuth = HTTPBasicAuth("test", "test")
        mocker.patch.object(auth.AuthDispatcher, "auth_method", auth_method)
        mock_fetch_get_token = mocker.patch.object(
            auth.AuthDispatcher, "get_token", return_value=token
        )
        mock_fetch_get_basic_credentials = mocker.patch.object(
            auth.AuthDispatcher, "get_basic_auth", return_value=basic_auth
        )
        assert auth.AuthDispatcher.auth_method == auth_method
        request_mock = mocker.Mock(headers={})

        if auth_method is None:
            auth.AuthDispatcher.auth(request_mock)
            mock_fetch_get_token.assert_not_called()
            mock_fetch_get_basic_credentials.assert_not_called()
            assert not request_mock.headers
        elif auth_method.startswith("token"):
            auth.AuthDispatcher.auth(request_mock)
            mock_fetch_get_token.assert_called_once()
            mock_fetch_get_basic_credentials.assert_not_called()
            assert "Authorization" in request_mock.headers
            assert "Bearer" in request_mock.headers["Authorization"]
        elif auth_method == "basic":
            auth.AuthDispatcher.auth(request_mock)
            mock_fetch_get_token.assert_not_called()
            mock_fetch_get_basic_credentials.assert_called_once()
            assert "Authorization" in request_mock.headers
            assert "Basic" in request_mock.headers["Authorization"]
        else:
            with pytest.raises(FhirException) as e:
                auth.AuthDispatcher.auth(request_mock)
            mock_fetch_get_token.assert_not_called()
            mock_fetch_get_basic_credentials.assert_not_called()
            assert "Unsupported token auth method" in str(e.value)

    def test_auth_dispatcher_get_token(
        self, mocker: MockFixture, mock_jose_jwt_encode: Mock
    ) -> None:
        token: str = "TOKEN"
        expiry: datetime = datetime.now() + timedelta(minutes=60)
        mock_fetch_token = mocker.patch.object(
            auth.AuthDispatcher, "fetch_token", return_value=(token, expiry)
        )
        assert auth.AuthDispatcher.token is None
        assert auth.AuthDispatcher.expired()
        auth.AuthDispatcher.get_token()
        mock_fetch_token.assert_called_once()
        assert auth.AuthDispatcher.token == token
        assert auth.AuthDispatcher.expiry == expiry

    def test_auth_dispatcher_get_basic_auth(self, mocker: MockFixture) -> None:
        cred = "test"
        mocker.patch.object(auth.fuego_config, "FHIR_SERVER_CLIENT_ID", new=cred)
        mocker.patch.object(auth.fuego_config, "FHIR_SERVER_CLIENT_SECRET", new=cred)
        expected: HTTPBasicAuth = HTTPBasicAuth(cred, cred)
        actual = auth.AuthDispatcher.get_basic_auth()
        assert expected == actual

    @pytest.mark.parametrize(
        "auth_method", ("basic", "token_basic", "token_epic", None)
    )
    def test_auth_dispatcher_fetch_token_base(
        self, mocker: MockFixture, auth_method: str, mock_jose_jwt_encode: Mock
    ) -> None:
        token: str = "TOKEN"
        expiry: datetime = datetime.now() + timedelta(minutes=60)
        mocker.patch.object(auth.AuthDispatcher, "auth_method", auth_method)
        mock_fetch_token_basic = mocker.patch.object(
            auth.AuthDispatcher, "_fetch_token_basic", return_value=(token, expiry)
        )
        mock_fetch_token_epic = mocker.patch.object(
            auth.AuthDispatcher, "_fetch_token_epic", return_value=(token, expiry)
        )
        assert auth.AuthDispatcher.auth_method == auth_method

        if auth_method is None or auth_method == "basic":
            with pytest.raises(FhirException) as e:
                auth.AuthDispatcher.fetch_token()
            mock_fetch_token_basic.assert_not_called()
            mock_fetch_token_epic.assert_not_called()
            assert "Unsupported token auth method" in str(e.value)
            return

        token_result: str
        expiry_result: datetime
        token_result, expiry_result = auth.AuthDispatcher.fetch_token()
        if auth_method == "token_basic":
            mock_fetch_token_basic.assert_called_once()
            mock_fetch_token_epic.assert_not_called()
        elif auth_method == "token_epic":
            mock_fetch_token_basic.assert_not_called()
            mock_fetch_token_epic.assert_called_once()

        assert token == token_result
        assert expiry == expiry_result

    @pytest.mark.parametrize("auth_method", ("token_basic", "token_epic"))
    def test_auth_dispatcher_fetch_token(
        self,
        mocker: MockFixture,
        auth_method: str,
        mock_jose_jwt_encode: Mock,
        mock_auth_success: Mock,
    ) -> None:
        mocker.patch.object(auth.AuthDispatcher, "auth_method", auth_method)
        auth.AuthDispatcher.get_token()
        assert mock_auth_success.called_once
        assert auth.AuthDispatcher.token == "TOKEN"
        assert auth.AuthDispatcher.expiry
        assert auth.AuthDispatcher.expiry > datetime.now()

    def test_auth_dispatcher_fetch_token_epic_jwt_error(
        self,
        mocker: MockFixture,
        mock_jose_jwt_encode: Mock,
        mock_auth_success: Mock,
    ) -> None:
        mocker.patch.object(auth.jose_jwt, "encode", side_effect=auth.jose_jwt.JWTError)
        mocker.patch.object(auth.AuthDispatcher, "auth_method", "token_epic")
        with pytest.raises(FhirException) as e:
            auth.AuthDispatcher.fetch_token()
        assert "Cannot encode the JWT claims" in str(e)

    @pytest.mark.parametrize("auth_method", ("token_basic", "token_epic"))
    def test_auth_dispatcher_fetch_token_auth_error(
        self,
        mocker: MockFixture,
        requests_mock: Mocker,
        auth_method: str,
        mock_jose_jwt_encode: Mock,
    ) -> None:
        mocker.patch.object(auth.AuthDispatcher, "auth_method", auth_method)
        mock_auth: Mock = requests_mock.post(
            Env().str("FHIR_SERVER_TOKEN_URL"),
            status_code=401,
        )
        with pytest.raises(FhirException) as e:
            auth.AuthDispatcher.get_token()
        assert mock_auth.called_once
        assert "Unexpected response from the auth server" in str(e.value)

    @pytest.mark.parametrize("auth_method", ("token_basic", "token_epic"))
    def test_auth_dispatcher_fetch_token_basic_connection_error(
        self,
        mocker: MockFixture,
        requests_mock: Mocker,
        auth_method: str,
        mock_jose_jwt_encode: Mock,
    ) -> None:
        mocker.patch.object(auth.AuthDispatcher, "auth_method", auth_method)
        mock_auth: Mock = requests_mock.post(
            Env().str("FHIR_SERVER_TOKEN_URL"),
            exc=requests.exceptions.ConnectionError,
        )
        with pytest.raises(FhirServerUnavailableException) as e:
            auth.AuthDispatcher.get_token()
        assert mock_auth.call_count == 1
        assert "Could not connect to the auth server" in str(e.value)
