from typing import Dict

import requests
from environs import Env
from requests import Response
from requests.auth import HTTPBasicAuth

env = Env()


def _get_base_url() -> str:
    return env.str("FHIR_SERVER_BASE_URL", "http://dhos-hapi-fhir-api:8080/fhir")


def _get_auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(
        env.str("FHIR_SERVER_CLIENT_ID"), env.str("FHIR_SERVER_CLIENT_SECRET")
    )


def patient_search(search_params: Dict) -> Response:
    return requests.get(
        f"{_get_base_url()}/Patient", params=search_params, timeout=15, auth=_get_auth()
    )


def patient_create(patient_details: Dict) -> Response:
    return requests.post(
        f"{_get_base_url()}/Patient", json=patient_details, timeout=90, auth=_get_auth()
    )


def expunge() -> Response:
    return requests.post(
        f"{_get_base_url()}/$expunge",
        json={
            "resourceType": "Parameters",
            "parameter": [{"name": "expungeEverything", "valueBoolean": True}],
        },
        timeout=15,
        auth=_get_auth(),
    )
