import json
import os
import signal
import socket
import sys
import time
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    NoReturn,
    Optional,
    Tuple,
    Type,
    Union,
)
from urllib.parse import urlparse

import pytest
from _pytest.config import Config
from flask import Flask, g
from flask_batteries_included.helpers import generate_uuid
from flask_batteries_included.sqldb import db
from flask_sqlalchemy import SQLAlchemy
from marshmallow import RAISE, Schema
from mock import Mock
from pytest_mock import MockerFixture, MockFixture
from requests_mock import Mocker

from dhos_fuego_api.config import fuego_config
from dhos_fuego_api.fhir.patient_tools import extract_name
from dhos_fuego_api.models.fhir_request import FhirRequest

#####################################################
# Configuration to use database started by tox-docker
#####################################################


def pytest_configure(config: Config) -> None:
    for env_var, tox_var in [
        ("DATABASE_HOST", "POSTGRES_HOST"),
        ("DATABASE_PORT", "POSTGRES_5432_TCP_PORT"),
    ]:
        if tox_var in os.environ:
            os.environ[env_var] = os.environ[tox_var]

    import logging

    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if os.environ.get("SQLALCHEMY_ECHO") else logging.WARNING
    )


def pytest_report_header(config: Config) -> str:
    db_config = (
        f"{os.environ['DATABASE_HOST']}:{os.environ['DATABASE_PORT']}"
        if os.environ.get("DATABASE_PORT")
        else "Sqlite"
    )
    return f"SQL database: {db_config}"


def _wait_for_it(service: str, timeout: int = 30) -> None:
    url = urlparse(service, scheme="http")

    host = url.hostname
    port = url.port or (443 if url.scheme == "https" else 80)

    friendly_name = f"{host}:{port}"

    def _handle_timeout(signum: Any, frame: Any) -> NoReturn:
        print(f"timeout occurred after waiting {timeout} seconds for {friendly_name}")
        sys.exit(1)

    if timeout > 0:
        signal.signal(signal.SIGALRM, _handle_timeout)
        signal.alarm(timeout)
        print(f"waiting {timeout} seconds for {friendly_name}")
    else:
        print(f"waiting for {friendly_name} without a timeout")

    t1 = time.time()

    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s = sock.connect_ex((host, port))
            if s == 0:
                seconds = round(time.time() - t1)
                print(f"{friendly_name} is available after {seconds} seconds")
                break
        except socket.gaierror:
            pass
        finally:
            time.sleep(1)

    signal.alarm(0)


#########################################################
# End Configuration to use database started by tox-docker
#########################################################


@pytest.fixture(scope="session")
def session_app() -> Flask:
    import dhos_fuego_api.app

    _wait_for_it(f"//{os.environ['DATABASE_HOST']}:{os.environ['DATABASE_PORT']}")

    app = dhos_fuego_api.app.create_app(testing=True)
    with app.app_context():
        db.drop_all()
        db.create_all()

    return app


@pytest.fixture(scope="session")
def _db(session_app: Flask) -> SQLAlchemy:
    """
    Provide the transactional fixtures with access to the database via a Flask-SQLAlchemy
    database connection.
    """
    return SQLAlchemy(app=session_app)


@pytest.fixture
def app(mocker: MockFixture, session_app: Flask) -> Flask:
    from flask_batteries_included.helpers.security import _ProtectedRoute

    def mock_claims(self: Any, verify: bool = True) -> Tuple:
        return g.jwt_claims, g.jwt_scopes

    mocker.patch.object(_ProtectedRoute, "_retrieve_jwt_claims", mock_claims)
    session_app.config["IGNORE_JWT_VALIDATION"] = False
    return session_app


@pytest.fixture
def app_context(app: Flask) -> Generator[None, None, None]:
    with app.app_context():
        yield


@pytest.fixture
def uses_sql_database(_db: SQLAlchemy) -> None:
    FhirRequest.query.delete()
    _db.session.commit()
    _db.drop_all()
    _db.create_all()


@pytest.fixture
def jwt_user_type() -> str:
    """parametrize to 'clinician', 'patient', or None as appropriate"""
    return "clinician"


@pytest.fixture
def clinician() -> str:
    """pytest-dhos:
    jwt_send_clinician_uuid/jwt_send_admin_uuid fixtures expect this for the uuid."""
    return generate_uuid()


@pytest.fixture
def gdm_clinician() -> str:
    """pytest-dhos:
    jwt_gdm_clinician_uuid/jwt_gdm_admin_uuid fixtures expect this for the uuid."""
    return generate_uuid()


@pytest.fixture
def jwt_scopes() -> Optional[Dict]:
    """parametrize to scopes required by a test"""
    return None


@pytest.fixture
def jwt_extra_claims() -> Dict:
    return {"can_edit_spo2_scale": True}


@pytest.fixture
def mock_bearer_validation(mocker: MockerFixture) -> Mock:
    from jose import jwt

    mocked = mocker.patch.object(jwt, "get_unverified_claims")
    mocked.return_value = {
        "sub": "1234567890",
        "name": "John Doe",
        "iat": 1_516_239_022,
        "iss": "http://localhost/",
    }
    return mocked


@pytest.fixture
def mock_auth_success(requests_mock: Mocker) -> Mock:
    return requests_mock.post(
        fuego_config.FHIR_SERVER_TOKEN_URL,
        json={"access_token": "TOKEN", "expires_in": 3600},
    )


@pytest.fixture
def assert_valid_schema(
    app: Flask,
) -> Callable[[Type[Schema], Union[Dict, List], bool], None]:
    def verify_schema(
        schema: Type[Schema], value: Union[Dict, List], many: bool = False
    ) -> None:
        # Roundtrip through JSON to convert datetime values to strings.
        serialised = json.loads(json.dumps(value, cls=app.json_encoder))
        schema().load(serialised, many=many, unknown=RAISE)

    return verify_schema


@pytest.fixture
def patient_mrn() -> str:
    return "123456"


@pytest.fixture
def patient_fhir_resource_id() -> str:
    return "00008b25-affc-4ec0-a401-593055df6fe8"


@pytest.fixture
def fhir_patient_request(patient_mrn: str) -> Dict:
    return {
        "resourceType": "Patient",
        "active": True,
        "identifier": [
            {
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MR",
                            "display": "Medical Record Number",
                        }
                    ]
                },
                "system": fuego_config.FHIR_SERVER_MRN_SYSTEM,
                "value": patient_mrn,
            }
        ],
        "name": [
            {
                "use": "official",
                "text": "Bezos, Jeff",
                "family": "Bezos",
                "given": [
                    "Jeff",
                ],
            }
        ],
        "birthDate": "1964-01-12",
    }


@pytest.fixture
def fhir_patient_response(
    fhir_patient_request: Dict, patient_fhir_resource_id: str
) -> Dict:
    return {**fhir_patient_request, "id": patient_fhir_resource_id}


@pytest.fixture
def fhir_patient_search_response(patient_mrn: str, fhir_patient_response: Dict) -> Dict:
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "link": [
            {"relation": "self", "url": f"Patient?identifier={patient_mrn}&_count=50"}
        ],
        "total": 1,
        "entry": [
            {
                "fullUrl": "https://api.dev.tju.commure.com/api/v1/r4/Patient/00008b25-affc-4ec0-a401-593055df6fe8",
                "resource": fhir_patient_response,
                "search": {"mode": "match"},
            }
        ],
        "identifier": [
            {
                "value": patient_mrn,
            }
        ],
    }


@pytest.fixture
def fuego_patient_create_request(fhir_patient_request: Dict) -> Dict:
    first_name, last_name = extract_name(fhir_patient_request)
    return {
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": fhir_patient_request["birthDate"],
        "mrn": fhir_patient_request["identifier"][0]["value"],
    }


@pytest.fixture
def fuego_patient_create_response(
    fuego_patient_create_request: Dict, patient_fhir_resource_id: str
) -> Dict:
    return {
        **fuego_patient_create_request,
        "fhir_resource_id": patient_fhir_resource_id,
    }
