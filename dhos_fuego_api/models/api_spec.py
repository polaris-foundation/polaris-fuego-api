from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask_batteries_included.helpers.apispec import (
    FlaskBatteriesPlugin,
    initialise_apispec,
    openapi_schema,
)
from marshmallow import EXCLUDE, Schema, fields

dhos_fuego_api_spec: APISpec = APISpec(
    version="1.0.0",
    openapi_version="3.0.3",
    title="DHOS Fuego API",
    info={"description": "A service for making requests to a FHIR server"},
    plugins=[FlaskPlugin(), MarshmallowPlugin(), FlaskBatteriesPlugin()],
)

initialise_apispec(dhos_fuego_api_spec)


@openapi_schema(dhos_fuego_api_spec)
class PatientSearchRequest(Schema):
    class Meta:
        description = "Patient search request"
        unknown = EXCLUDE
        ordered = True

    mrn = fields.String(
        required=True, description="MRN or hospital number", example="123456"
    )


@openapi_schema(dhos_fuego_api_spec)
class PatientSearchResponse(Schema):
    class Meta:
        description = "Patient search response"
        unknown = EXCLUDE
        ordered = True

    fhir_resource_id = fields.String(
        required=True,
        description="ID of the resource on the FHIR server",
        example="5690f87c-c23a-4fa0-95a7-d803aff2b8e0",
    )
    first_name = fields.String(
        required=True, description="First name", example="Elizabeth"
    )
    last_name = fields.String(required=True, description="Last name", example="Windsor")
    date_of_birth = fields.Date(
        required=True, description="Patient's date of birth", example="1926-04-21"
    )
    mrn = fields.String(
        required=True, description="MRN or hospital number", example="123456"
    )


@openapi_schema(dhos_fuego_api_spec)
class PatientCreateRequest(Schema):
    class Meta:
        description = "Patient create request"
        unknown = EXCLUDE
        ordered = True

    first_name = fields.String(
        required=True, description="First name", example="Elizabeth"
    )
    last_name = fields.String(required=True, description="Last name", example="Windsor")
    date_of_birth = fields.Date(
        required=True, description="Patient's date of birth", example="1926-04-21"
    )
    mrn = fields.String(
        required=True, description="MRN or hospital number", example="123456"
    )


@openapi_schema(dhos_fuego_api_spec)
class PatientCreateResponse(PatientCreateRequest):
    class Meta:
        description = "Patient create response"
        unknown = EXCLUDE
        ordered = True

    fhir_resource_id = fields.String(
        required=True,
        description="ID of the resource on the FHIR server",
        example="5690f87c-c23a-4fa0-95a7-d803aff2b8e0",
    )
