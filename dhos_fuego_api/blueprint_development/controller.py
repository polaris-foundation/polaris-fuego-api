from datetime import datetime
from typing import Dict, List, Sequence

from flask_batteries_included.sqldb import db
from she_logging.logging import logger

from dhos_fuego_api.config import fuego_config
from dhos_fuego_api.fhir import client
from dhos_fuego_api.fhir.patient_tools import extract_name, extract_patients
from dhos_fuego_api.models.fhir_request import FhirRequest

ALL_MODELS: Sequence[db.Model] = [FhirRequest]


def reset_database() -> None:
    """Drops SQL data"""
    try:
        for model in ALL_MODELS:
            db.session.query(model).delete()
        db.session.commit()
    except Exception:
        logger.exception("Drop SQL data failed")
        db.session.rollback()


def reset_fhir_database() -> None:
    logger.info("Performing FHIR EPR `$expunge` operation...")
    client.expunge()
    logger.info("FHIR EPR data has been successfully expunged.")


def patient_search() -> List[Dict]:
    fhir_request: FhirRequest = client.patient_search()
    db.session.add(fhir_request)
    db.session.commit()
    logger.debug("Recorded FHIR request (UUID %s)", fhir_request.uuid)
    return extract_patients(fhir_request=fhir_request)


def patient_create(patient_details: Dict) -> Dict:
    fhir_patient_details = {
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
                "value": patient_details["mrn"],
            }
        ],
        "name": [
            {
                "use": "official",
                "text": f"{patient_details['last_name']}, {patient_details['first_name']}",
                "family": patient_details["last_name"],
                "given": [
                    patient_details["first_name"],
                ],
            }
        ],
        "birthDate": datetime.fromisoformat(patient_details["date_of_birth"]).strftime(
            "%Y-%m-%d"
        ),
    }

    fhir_request: FhirRequest = client.patient_create(
        patient_details=fhir_patient_details
    )
    db.session.add(fhir_request)
    db.session.commit()
    logger.debug("Recorded FHIR request (UUID %s)", fhir_request.uuid)

    first_name, last_name = extract_name(patient=fhir_request.response_body)
    return {
        "fhir_resource_id": fhir_request.response_body["id"],
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": fhir_request.response_body["birthDate"],
        "mrn": fhir_request.response_body["identifier"][0]["value"],
    }
