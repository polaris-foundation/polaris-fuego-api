import time
from typing import Dict, List

from flask import Blueprint, Response, current_app, jsonify
from flask_batteries_included.helpers.security import protected_route
from flask_batteries_included.helpers.security.endpoint_security import key_present

from dhos_fuego_api.blueprint_development import controller

development_blueprint = Blueprint("dhos/dev", __name__)


@development_blueprint.route("/drop_data", methods=["POST"])
@protected_route(key_present("system_id"))
def drop_data_route() -> Response:
    """
    ---
    post:
      summary: Drop data
      description: Drops dhos-fuego-api and FHIR EPR databases. Dev-only
      tags: [dev]
      responses:
        '200':
          description: Drop results
          content:
            application/json:
              schema:
                type: object
                properties:
                  complete:
                    type: boolean
                  time_taken:
                    type: integer
        default:
          description: >-
            Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    if current_app.config["ALLOW_DROP_DATA"] is not True:
        raise PermissionError("Cannot drop data in this environment")

    start = time.time()
    controller.reset_database()
    controller.reset_fhir_database()
    total_time = time.time() - start

    return jsonify({"complete": True, "time_taken": str(total_time) + "s"})


@development_blueprint.route("/dhos/v1/patient_search", methods=["GET"])
@protected_route(key_present("system_id"))
def patient_search() -> Response:
    """
    ---
    get:
      summary: Get all patients from FHIR EPR database
      description: Patient search without parameters. Returns all patients. Dev-only.
      tags: [dev]
      responses:
        '200':
          description: Patients list
          content:
            application/json:
              schema:
                type: array
                items: PatientSearchResponse
        default:
          description: >-
            Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    results: List[Dict] = controller.patient_search()
    return jsonify(results)


@development_blueprint.route("/dhos/v1/patient_create", methods=["POST"])
@protected_route(key_present("system_id"))
def patient_create(patient_details: Dict) -> Response:
    """
    ---
    post:
      summary: Create patient
      description: Creates patient in FHIR EPR system. Dev-only.
      tags: [dev]
      requestBody:
        description: Patient details
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatientCreateRequest'
              x-body-name: patient_details
      responses:
        '200':
          description: Create results
          content:
            application/json:
              schema:
                type: array
                items: PatientCreateResponse
        default:
          description: >-
            Error, e.g. 400 Bad Request, 503 Service Unavailable
          content:
            application/json:
              schema: Error
    """
    result: Dict = controller.patient_create(patient_details=patient_details)
    response: Response = jsonify(result)
    response.status_code = 201
    return response
