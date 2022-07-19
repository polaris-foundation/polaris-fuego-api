from typing import Dict

import requests
from environs import Env
from requests import Response


def _get_base_url() -> str:
    return Env().str("DHOS_FUEGO_API_URL", "http://dhos-fuego-api:5000")


def patient_search(search_details: Dict, jwt: str) -> Response:
    return requests.post(
        f"{_get_base_url()}/dhos/v1/patient_search",
        headers={"Authorization": f"Bearer {jwt}"},
        json=search_details,
        timeout=15,
    )


def patient_create(patient_details: Dict, jwt: str) -> Response:
    return requests.post(
        f"{_get_base_url()}/dhos/v1/patient_create",
        headers={"Authorization": f"Bearer {jwt}"},
        json=patient_details,
        timeout=90,
    )


def drop_data(jwt: str) -> Response:
    return requests.post(
        f"{_get_base_url()}/drop_data",
        headers={"Authorization": f"Bearer {jwt}"},
        timeout=30,
    )
