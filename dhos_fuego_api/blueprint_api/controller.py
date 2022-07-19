from typing import Dict, List

from flask_batteries_included.sqldb import db
from she_logging import logger

from dhos_fuego_api.fhir import client
from dhos_fuego_api.fhir.patient_tools import extract_patients
from dhos_fuego_api.models.fhir_request import FhirRequest


def patient_search(search_details: Dict) -> List[Dict]:
    # Make request and record it in the database.
    fhir_request: FhirRequest = client.patient_search(mrn=search_details["mrn"])
    db.session.add(fhir_request)
    db.session.commit()
    logger.debug("Recorded FHIR request (UUID %s)", fhir_request.uuid)
    return extract_patients(
        fhir_request=fhir_request, validate_mrn=True, search_details=search_details
    )
