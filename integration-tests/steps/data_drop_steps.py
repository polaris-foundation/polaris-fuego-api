from behave import step
from behave.runner import Context
from clients import fuego_client
from requests import Response


@step("I perform data drop")
def expunge_fhir(context: Context) -> None:
    response: Response = fuego_client.drop_data(context.system_jwt)
    assert response.status_code == 200
    data_drop_results = response.json()
    assert data_drop_results.get("complete")
