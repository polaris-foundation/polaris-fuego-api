import uuid
from typing import Dict, Optional

import pytest
from marshmallow import RAISE
from mock import Mock
from pytest_mock import MockFixture

from dhos_fuego_api.blueprint_api import controller
from dhos_fuego_api.blueprint_development import controller as dev_controller
from dhos_fuego_api.fhir import client
from dhos_fuego_api.fhir.patient_tools import extract_mrn, extract_name
from dhos_fuego_api.models.api_spec import PatientCreateResponse, PatientSearchResponse
from dhos_fuego_api.models.fhir_request import FhirRequest


@pytest.mark.usefixtures("app")
class TestController:
    def test_patient_search(
        self, mocker: MockFixture, patient_mrn: str, fhir_patient_search_response: Dict
    ) -> None:
        # Arrange
        used_url = f"https://someurl.com/{uuid.uuid4()}"
        mock_search_patients: Mock = mocker.patch.object(
            client,
            "patient_search",
            return_value=FhirRequest(
                request_url=used_url,
                request_body=None,
                response_body=fhir_patient_search_response,
            ),
        )

        # Act
        results = controller.patient_search(search_details={"mrn": patient_mrn})

        # Assert
        PatientSearchResponse().load(results, many=True, unknown=RAISE)
        mock_search_patients.assert_called_once_with(mrn=patient_mrn)
        fhir_request: Optional[FhirRequest] = FhirRequest.query.filter_by(
            request_url=used_url
        ).first()
        assert fhir_request is not None
        assert fhir_request.request_url == used_url
        assert fhir_request.request_body is None
        assert fhir_request.response_body == fhir_patient_search_response
        p = fhir_patient_search_response["entry"][0]["resource"]
        assert results == [
            {
                "fhir_resource_id": p["id"],
                "first_name": p["name"][0]["given"][0],
                "last_name": p["name"][0]["family"],
                "mrn": patient_mrn,
                "date_of_birth": p["birthDate"],
            }
        ]

    def test_patient_search_excluded(
        self, mocker: MockFixture, patient_mrn: str, fhir_patient_search_response: Dict
    ) -> None:
        """Tests that patients without a name or without a matching MRN are excluded"""
        # Arrange
        fhir_patient_search_response["entry"] = [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "example1",
                    "name": [],
                    "identifier": [
                        {
                            "use": "usual",
                            "type": {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                        "code": "MR",
                                    }
                                ]
                            },
                            "value": patient_mrn,
                        },
                    ],
                }
            },
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "example2",
                    "name": [
                        {
                            "use": "official",
                            "family": "Chalmers",
                            "given": ["Peter", "James"],
                        }
                    ],
                    "identifier": [],
                }
            },
        ]
        used_url = f"https://someurl.com/{uuid.uuid4()}"
        mock_search_patients: Mock = mocker.patch.object(
            client,
            "patient_search",
            return_value=FhirRequest(
                request_url=used_url,
                request_body=None,
                response_body=fhir_patient_search_response,
            ),
        )

        # Act
        results = controller.patient_search(search_details={"mrn": patient_mrn})

        # Assert
        assert results == []

    def test_extract_name_multiple(self) -> None:
        patient = {
            "resourceType": "Patient",
            "id": "example",
            "name": [
                {"use": "official", "family": "Chalmers", "given": ["Peter", "James"]},
                {"use": "usual", "given": ["Jim"]},
                {
                    "use": "maiden",
                    "family": "Windsor",
                    "given": ["Peter", "James"],
                    "period": {"end": "2002"},
                },
            ],
        }
        first_name, last_name = extract_name(patient)
        assert first_name == "Jim"
        assert last_name == "Chalmers"

    def test_extract_name_none(self) -> None:
        patient: Dict = {"resourceType": "Patient", "id": "example", "name": []}
        first_name, last_name = extract_name(patient)
        assert first_name == ""
        assert last_name == ""

    def test_validate_mrn(self) -> None:
        patient = {
            "resourceType": "Patient",
            "id": "example",
            "identifier": [
                {
                    "use": "usual",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "MR",
                            }
                        ]
                    },
                    "system": "urn:oid:1.2.36.146.595.217.0.1",
                    "value": "12345",
                    "period": {"start": "2001-05-06"},
                    "assigner": {"display": "Acme Healthcare"},
                },
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "SOMETHINGELSE",
                            }
                        ]
                    },
                    "system": "urn:oid:1.2.36.146.595.217.0.1",
                    "value": "77777",
                },
            ],
        }
        assert extract_mrn(patient, "12345") is not None
        assert extract_mrn(patient, "77777") is None
        assert extract_mrn(patient, "993344") is None


@pytest.mark.usefixtures("app")
class TestDevController:
    def test_patient_search(
        self, mocker: MockFixture, fhir_patient_search_response: Dict
    ) -> None:
        # Arrange
        used_url = f"https://someurl.com/{uuid.uuid4()}"
        mock_search_patients: Mock = mocker.patch.object(
            client,
            "patient_search",
            return_value=FhirRequest(
                request_url=used_url,
                request_body=None,
                response_body=fhir_patient_search_response,
            ),
        )

        # Act
        results = dev_controller.patient_search()

        # Assert
        PatientSearchResponse().load(results, many=True, unknown=RAISE)
        mock_search_patients.assert_called_once()
        fhir_request: Optional[FhirRequest] = FhirRequest.query.filter_by(
            request_url=used_url
        ).first()
        assert fhir_request is not None
        assert fhir_request.request_url == used_url
        assert fhir_request.request_body is None
        assert fhir_request.response_body == fhir_patient_search_response
        p = fhir_patient_search_response["entry"][0]["resource"]
        assert results == [
            {
                "fhir_resource_id": p["id"],
                "first_name": p["name"][0]["given"][0],
                "last_name": p["name"][0]["family"],
                "mrn": p["identifier"][0]["value"],
                "date_of_birth": p["birthDate"],
            }
        ]

    def test_patient_create(
        self,
        mocker: MockFixture,
        patient_mrn: str,
        fuego_patient_create_request: Dict,
        fhir_patient_request: Dict,
        fhir_patient_response: Dict,
    ) -> None:
        # Arrange
        used_url = f"https://someurl.com/{uuid.uuid4()}"
        mock_create_patient: Mock = mocker.patch.object(
            client,
            "patient_create",
            return_value=FhirRequest(
                request_url=used_url,
                request_body=fhir_patient_request,
                response_body=fhir_patient_response,
            ),
        )

        # Act
        result = dev_controller.patient_create(
            patient_details=fuego_patient_create_request
        )

        # Assert
        PatientCreateResponse().load(result, many=False, unknown=RAISE)
        mock_create_patient.assert_called_once_with(
            patient_details=fhir_patient_request
        )
        fhir_request: Optional[FhirRequest] = FhirRequest.query.filter_by(
            request_url=used_url
        ).first()
        assert fhir_request is not None
        assert fhir_request.request_url == used_url
        assert fhir_request.request_body == fhir_patient_request
        assert fhir_request.response_body == fhir_patient_response
        assert result == {
            "fhir_resource_id": fhir_request.response_body["id"],
            "first_name": fhir_request.response_body["name"][0]["given"][0],
            "last_name": fhir_request.response_body["name"][0]["family"],
            "date_of_birth": fhir_request.response_body["birthDate"],
            "mrn": fhir_request.response_body["identifier"][0]["value"],
        }
