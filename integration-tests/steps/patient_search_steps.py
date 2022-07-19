from typing import Dict, List

from behave import then, when
from behave.runner import Context
from clients import fuego_client
from requests import Response


@when("I search for the patient by MRN")
def patient_search(context: Context) -> None:
    response: Response = fuego_client.patient_search(
        search_details={"mrn": context.patient_details["mrn"]}, jwt=context.system_jwt
    )
    assert response.status_code == 200
    context.search_response = response


@then("I see the expected patient in search results")
def check_search_results(context: Context) -> None:
    response_data: List = context.search_response.json()
    assert response_data
    patient_details: Dict = response_data[0]
    assert patient_details["mrn"] == context.patient_details["mrn"]
    assert patient_details["first_name"] == context.patient_details["first_name"]
    assert patient_details["last_name"] == context.patient_details["last_name"]
    assert patient_details["date_of_birth"] == context.patient_details["date_of_birth"]
    assert patient_details["fhir_resource_id"] is not None


@then("I see no patients in search results")
def check_no_search_results(context: Context) -> None:
    response_data: List = context.search_response.json()
    assert response_data is not None
    assert not response_data
