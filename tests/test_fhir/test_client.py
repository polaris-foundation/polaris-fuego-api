from typing import Dict

import pytest
import requests
from flask import Flask
from mock import Mock
from requests_mock import Mocker

from dhos_fuego_api.config import fuego_config
from dhos_fuego_api.fhir import auth, client
from dhos_fuego_api.fhir.error_handler import (
    FhirException,
    FhirServerUnavailableException,
)
from dhos_fuego_api.models.fhir_request import FhirRequest


class TestClient:
    @pytest.fixture(autouse=True)
    def clear_token_cache(self) -> None:
        auth.AuthDispatcher.clear()

    def test_patient_search(
        self,
        app: Flask,
        requests_mock: Mocker,
        mock_auth_success: Mock,
        fhir_patient_search_response: Dict,
    ) -> None:
        # Arrange
        mrn = "123456"
        mock_fhir_request: Mock = requests_mock.get(
            f"{fuego_config.FHIR_SERVER_BASE_URL}/Patient?identifier={fuego_config.FHIR_SERVER_MRN_SYSTEM}%7C{mrn}",
            json=fhir_patient_search_response,
        )

        # Act
        fhir_request: FhirRequest = client.patient_search(mrn=mrn)

        # Assert
        assert fhir_request.response_body == fhir_patient_search_response
        assert (
            fhir_request.request_url
            == f"{fuego_config.FHIR_SERVER_BASE_URL}/Patient?identifier={fuego_config.FHIR_SERVER_MRN_SYSTEM}%7C{mrn}"
        )
        assert mock_fhir_request.call_count == 1
        assert mock_auth_success.call_count == 1

    def test_patient_search_all(
        self,
        app: Flask,
        requests_mock: Mocker,
        mock_auth_success: Mock,
        fhir_patient_search_response: Dict,
    ) -> None:
        # Arrange
        mock_fhir_request: Mock = requests_mock.get(
            f"{fuego_config.FHIR_SERVER_BASE_URL}/Patient",
            json=fhir_patient_search_response,
        )

        # Act
        fhir_request: FhirRequest = client.patient_search()

        # Assert
        assert fhir_request.response_body == fhir_patient_search_response
        assert (
            fhir_request.request_url == f"{fuego_config.FHIR_SERVER_BASE_URL}/Patient"
        )
        assert mock_fhir_request.call_count == 1
        assert mock_auth_success.call_count == 1

    def test_patient_search_auth_error(
        self,
        app: Flask,
        requests_mock: Mocker,
        mock_auth_success: Mock,
        fhir_patient_search_response: Dict,
    ) -> None:
        # Arrange
        mrn = "123456"
        mock_fhir_request: Mock = requests_mock.get(
            f"{fuego_config.FHIR_SERVER_BASE_URL}/Patient?identifier={fuego_config.FHIR_SERVER_MRN_SYSTEM}%7C{mrn}",
            status_code=401,
            json={"error": "invalid_client", "error_description": "access denied"},
        )

        # Act
        with pytest.raises(FhirException) as e:
            client.patient_search(mrn=mrn)

        # Assert
        assert mock_fhir_request.call_count == 1
        assert "Unexpected response from the FHIR server" in str(e.value)

    def test_patient_search_connection_error(
        self,
        app: Flask,
        requests_mock: Mocker,
        mock_auth_success: Mock,
        fhir_patient_search_response: Dict,
    ) -> None:
        mrn = "123456"
        mock_fhir_request: Mock = requests_mock.get(
            f"{fuego_config.FHIR_SERVER_BASE_URL}/Patient?identifier={fuego_config.FHIR_SERVER_MRN_SYSTEM}%7C{mrn}",
            exc=requests.exceptions.Timeout,
        )

        # Act
        with pytest.raises(FhirServerUnavailableException) as e:
            client.patient_search(mrn=mrn)

        # Assert
        assert mock_fhir_request.call_count == 1
        assert "Could not connect to the FHIR server" in str(e.value)

    def test_patient_create(
        self,
        app: Flask,
        requests_mock: Mocker,
        mock_auth_success: Mock,
        fhir_patient_request: Dict,
        fhir_patient_response: Dict,
    ) -> None:
        mock_fhir_request: Mock = requests_mock.post(
            f"{fuego_config.FHIR_SERVER_BASE_URL}/Patient", json=fhir_patient_response
        )
        fhir_request: FhirRequest = client.patient_create(
            patient_details=fhir_patient_request
        )
        assert fhir_request.response_body == fhir_patient_response
        assert (
            fhir_request.request_url == f"{fuego_config.FHIR_SERVER_BASE_URL}/Patient"
        )
        assert mock_fhir_request.call_count == 1
        assert mock_auth_success.call_count == 1

    def test_patient_create_auth_error(
        self,
        app: Flask,
        requests_mock: Mocker,
        mock_auth_success: Mock,
        fhir_patient_request: Dict,
    ) -> None:
        # Arrange
        mock_fhir_request: Mock = requests_mock.post(
            f"{fuego_config.FHIR_SERVER_BASE_URL}/Patient",
            status_code=401,
            json={"error": "invalid_client", "error_description": "access denied"},
        )

        # Act
        with pytest.raises(FhirException) as e:
            client.patient_create(patient_details=fhir_patient_request)

        # Assert
        assert mock_fhir_request.call_count == 1
        assert "Unexpected response from the FHIR server" in str(e.value)

    def test_patient_create_connection_error(
        self,
        app: Flask,
        requests_mock: Mocker,
        mock_auth_success: Mock,
        fhir_patient_request: Dict,
    ) -> None:
        mock_fhir_request: Mock = requests_mock.post(
            f"{fuego_config.FHIR_SERVER_BASE_URL}/Patient",
            exc=requests.exceptions.Timeout,
        )

        # Act
        with pytest.raises(FhirServerUnavailableException) as e:
            client.patient_create(patient_details=fhir_patient_request)

        # Assert
        assert mock_fhir_request.call_count == 1
        assert "Could not connect to the FHIR server" in str(e.value)
