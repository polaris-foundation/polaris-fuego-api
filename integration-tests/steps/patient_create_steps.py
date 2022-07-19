import faker
from behave import step
from behave.runner import Context
from clients import fuego_client


@step("a patient is present in EPR")
def create_patient(context: Context) -> None:
    fake = faker.Faker()

    patient_details = {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "date_of_birth": fake.date(),
        "mrn": fake.ssn(),
    }

    context.patient_details = patient_details
    response = fuego_client.patient_create(
        patient_details=patient_details, jwt=context.system_jwt
    )
    response.raise_for_status()
    assert response.status_code == 201
