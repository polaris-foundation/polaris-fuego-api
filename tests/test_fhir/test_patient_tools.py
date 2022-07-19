from typing import Dict

from dhos_fuego_api.fhir import patient_tools


class TestPatientTools:
    def test_extract_mrn_with_system(
        self, fhir_patient_search_response: Dict, patient_mrn: str
    ) -> None:
        patient = fhir_patient_search_response["entry"][0]["resource"]
        extracted_mrn = patient_tools.extract_mrn(patient=patient)
        assert extracted_mrn is not None
        assert extracted_mrn == patient_mrn

    def test_extract_mrn_with_coding(
        self, fhir_patient_search_response: Dict, patient_mrn: str
    ) -> None:
        patient = fhir_patient_search_response["entry"][0]["resource"]

        patient["identifier"][0]["type"] = {
            "coding": [
                {
                    "code": "MR",
                },
                {"code": "not MR"},
            ]
        }

        extracted_mrn = patient_tools.extract_mrn(patient=patient)
        assert extracted_mrn is not None
        assert extracted_mrn == patient_mrn

    def test_extract_mrn_with_validation(
        self, fhir_patient_search_response: Dict, patient_mrn: str
    ) -> None:
        patient = fhir_patient_search_response["entry"][0]["resource"]
        extracted_mrn = patient_tools.extract_mrn(
            patient=patient, expected_mrn=patient_mrn
        )
        assert extracted_mrn is not None
        assert extracted_mrn == patient_mrn

    def test_extract_mrn_no_valid_mrn(
        self, fhir_patient_search_response: Dict, patient_mrn: str
    ) -> None:
        patient = fhir_patient_search_response["entry"][0]["resource"]
        patient["identifier"][0]["value"] = "some other mrn"
        extracted_mrn = patient_tools.extract_mrn(
            patient=patient, expected_mrn=patient_mrn
        )
        assert extracted_mrn is None
        assert extracted_mrn != patient_mrn
