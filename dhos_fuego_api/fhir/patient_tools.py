from typing import Dict, List, Optional, Tuple

from she_logging import logger

from dhos_fuego_api.config import fuego_config
from dhos_fuego_api.models.fhir_request import FhirRequest


def extract_name(patient: Dict) -> Tuple[str, str]:
    """
    FHIR Patient resources potentially have multiple names: http://hl7.org/fhir/datatypes.html#HumanName
    Choose a first name / last name based on the following order:
    1) Any "usual" name (take the first if there are multiple)
    2) Any "official" name (take the first if there are multiple)
    3) Any other type of name (take the first if there are multiple)
    """
    usual_name: Dict = next((n for n in patient["name"] if n["use"] == "usual"), {})
    official_name: Dict = next(
        (n for n in patient["name"] if n["use"] == "official"), {}
    )
    other_name: Dict = next(
        iter(patient["name"]),
        {},
    )
    possible_first_names: List[str] = [
        *usual_name.get("given", []),
        *official_name.get("given", []),
        *other_name.get("given", []),
        "",
    ]
    first_name: str = possible_first_names[0]
    last_name: str = (
        usual_name.get("family")
        or official_name.get("family")
        or other_name.get("family")
        or ""
    )
    return first_name, last_name


def extract_mrn(patient: Dict, expected_mrn: Optional[str] = None) -> Optional[str]:
    """
    FHIR identifier resource: http://hl7.org/fhir/datatypes.html#Identifier
    Code system: https://terminology.hl7.org/2.0.0/CodeSystem-v2-0203.html
    """
    for identifier in patient["identifier"]:
        identifier_value = identifier.get("value")

        # according to a FHIR specification, identifier should have codings
        codings: List[Dict] = identifier.get("type", {}).get("coding", [])
        for coding in codings:
            if coding.get("code") == "MR":
                if expected_mrn:
                    if identifier_value == expected_mrn:
                        return identifier_value
                    continue
                return identifier_value

        # if the FHIR EPR doesn't follow the specification, we check mrn system
        mrn_system: Optional[str] = identifier.get("system")
        if mrn_system and mrn_system == fuego_config.FHIR_SERVER_MRN_SYSTEM:
            if expected_mrn:
                if identifier_value == expected_mrn:
                    return identifier_value
                continue
            return identifier_value

    return None


def extract_patients(
    fhir_request: FhirRequest,
    validate_mrn: bool = False,
    search_details: Optional[Dict] = None,
) -> List[Dict]:
    if not fhir_request.response_body.get("total", 0):
        logger.debug("No entries found (UUID %s)", fhir_request.uuid)
        return []

    # Parse FHIR response to list of patient resources.
    patients: List[Dict] = [e["resource"] for e in fhir_request.response_body["entry"]]
    logger.debug("Found %d patients", len(patients))

    # Trim patient resource list to salient information.
    trimmed_patients: List[Dict] = []
    for patient in patients:
        fhir_resource_id: str = patient["id"]
        first_name, last_name = extract_name(patient)
        if not first_name and not last_name:
            logger.warning(
                "Could not extract name for patient, skipping FHIR resource %s",
                fhir_resource_id,
            )
            continue

        expected_mrn: Optional[str] = (
            search_details["mrn"] if validate_mrn and search_details else None
        )
        actual_mrn: Optional[str] = extract_mrn(
            patient=patient, expected_mrn=expected_mrn if expected_mrn else None
        )

        if expected_mrn and actual_mrn is None:
            logger.warning(
                "Patient does not have the expected MRN, skipping FHIR resource %s",
                fhir_resource_id,
            )
            continue

        trimmed_patients.append(
            {
                "fhir_resource_id": fhir_resource_id,
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": patient["birthDate"],
                "mrn": actual_mrn,
            }
        )

    return trimmed_patients
