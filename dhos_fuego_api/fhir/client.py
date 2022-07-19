from typing import Callable, Dict, Optional

import requests
from she_logging import logger

from dhos_fuego_api.config import fuego_config
from dhos_fuego_api.fhir.auth import AuthDispatcher
from dhos_fuego_api.fhir.error_handler import (
    FhirException,
    FhirServerUnavailableException,
)
from dhos_fuego_api.models.fhir_request import FhirRequest


def _make_fhir_request(
    endpoint: str,
    method: str,
    params: Optional[Dict] = None,
    json: Optional[Dict] = None,
) -> requests.Response:
    actual_method: Callable = getattr(requests, method)
    try:
        response: requests.Response = actual_method(
            url=f"{fuego_config.FHIR_SERVER_BASE_URL}/{endpoint}",
            params=params,
            json=json,
            headers={"Accept": "application/fhir+json"},
            auth=AuthDispatcher.auth,
        )
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.exception(
            "Unexpected response from FHIR server: HTTP %s",
            e.response.status_code,
            extra={"response_body": e.response.text},
        )
        raise FhirException("Unexpected response from the FHIR server")
    except requests.RequestException:
        raise FhirServerUnavailableException("Could not connect to the FHIR server")

    return response


def expunge() -> requests.Response:
    json_body = {
        "resourceType": "Parameters",
        "parameter": [{"name": "expungeEverything", "valueBoolean": True}],
    }
    return _make_fhir_request(endpoint="$expunge", method="post", json=json_body)


def patient_search(mrn: Optional[str] = None) -> FhirRequest:
    params: Optional[Dict]
    if mrn:
        logger.debug("Searching FHIR server for patients with MRN %s", mrn)
        params = {"identifier": f"{fuego_config.FHIR_SERVER_MRN_SYSTEM}|{mrn}"}
    else:
        logger.debug("Searching for all patients")
        params = None

    response = _make_fhir_request(endpoint="Patient", method="get", params=params)

    return FhirRequest(
        request_url=response.url,
        request_body=None,
        response_body=response.json(),
    )


def patient_create(patient_details: Dict) -> FhirRequest:
    logger.debug("Creating new patient", extra={"patient_details": patient_details})
    response = _make_fhir_request(
        endpoint="Patient", method="post", json=patient_details
    )
    return FhirRequest(
        request_url=response.url,
        request_body=patient_details,
        response_body=response.json(),
    )
