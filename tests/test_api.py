from typing import Dict
from unittest.mock import Mock

import pytest
from flask.testing import FlaskClient
from pytest_mock import MockFixture

from dhos_fuego_api.blueprint_api import controller
from dhos_fuego_api.blueprint_development import controller as dev_controller


class TestApi:
    @pytest.mark.usefixtures("app", "mock_bearer_validation", "jwt_gdm_clinician_uuid")
    def test_patient_search_success(
        self, client: FlaskClient, mocker: MockFixture
    ) -> None:
        mock_search: Mock = mocker.patch.object(
            controller, "patient_search", return_value=[{"mrn": 123456}]
        )
        response = client.post(
            "/dhos/v1/patient_search",
            json={"mrn": "123456"},
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        mock_search.assert_called_once_with(search_details={"mrn": "123456"})

    @pytest.mark.usefixtures("app", "mock_bearer_validation", "jwt_gdm_clinician_uuid")
    def test_patient_search_invalid_request(self, client: FlaskClient) -> None:
        response = client.post(
            "/dhos/v1/patient_search",
            json={"something": "123456"},
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    @pytest.mark.usefixtures("app", "mock_bearer_validation", "jwt_gdm_clinician_uuid")
    def test_patient_search_no_auth(self, client: FlaskClient) -> None:
        response = client.post(
            "/dhos/v1/patient_search",
            json={"mrn": "123456"},
        )
        assert response.status_code == 401


class TestDevApi:
    @pytest.mark.usefixtures("app", "mock_bearer_validation", "jwt_system")
    def test_patient_search_success(
        self, client: FlaskClient, mocker: MockFixture
    ) -> None:
        mock_search: Mock = mocker.patch.object(
            dev_controller, "patient_search", return_value=[{"mrn": 123456}]
        )
        response = client.get(
            "/dhos/v1/patient_search",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 200
        mock_search.assert_called_once()

    @pytest.mark.usefixtures("app", "mock_bearer_validation", "jwt_gdm_clinician_uuid")
    def test_patient_search_403(self, client: FlaskClient, mocker: MockFixture) -> None:
        mock_search: Mock = mocker.patch.object(
            dev_controller, "patient_search", return_value=[{"mrn": 123456}]
        )
        response = client.get(
            "/dhos/v1/patient_search",
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 403
        mock_search.assert_not_called()

    @pytest.mark.usefixtures("app", "mock_bearer_validation", "jwt_system")
    def test_patient_create_success(
        self,
        client: FlaskClient,
        mocker: MockFixture,
        fuego_patient_create_request: Dict,
        fuego_patient_create_response: Dict,
    ) -> None:
        mock_create: Mock = mocker.patch.object(
            dev_controller, "patient_create", return_value=fuego_patient_create_response
        )
        response = client.post(
            "/dhos/v1/patient_create",
            json=fuego_patient_create_request,
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 201
        mock_create.assert_called_once_with(
            patient_details=fuego_patient_create_request
        )
        assert response.json == fuego_patient_create_response

    @pytest.mark.usefixtures("app", "mock_bearer_validation", "jwt_system")
    def test_patient_create_invalid_request(self, client: FlaskClient) -> None:
        response = client.post(
            "/dhos/v1/patient_create",
            json={"something": "123456"},
            headers={"Authorization": "Bearer TOKEN"},
        )
        assert response.status_code == 400

    @pytest.mark.usefixtures("app", "mock_bearer_validation", "jwt_system")
    def test_patient_create_no_auth(self, client: FlaskClient) -> None:
        response = client.post(
            "/dhos/v1/patient_create",
            json={"something": "123456"},
        )
        assert response.status_code == 401
