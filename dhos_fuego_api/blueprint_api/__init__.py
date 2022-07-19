from typing import Dict, List

from flask import Blueprint, Response, jsonify
from flask_batteries_included.helpers.security import protected_route
from flask_batteries_included.helpers.security.endpoint_security import (
    or_,
    scopes_present,
)

from dhos_fuego_api.blueprint_api import controller

fuego_blueprint = Blueprint("fuego_api", __name__)


@fuego_blueprint.route("/dhos/v1/patient_search", methods=["POST"])
@protected_route(
    or_(
        scopes_present(required_scopes="read:patient"),
        scopes_present(required_scopes="read:gdm_patient"),
        scopes_present(required_scopes="read:gdm_patient_all"),
    )
)
def patient_search(search_details: Dict) -> Response:
    """
    ---
    post:
      summary: Search patients
      description: Search a FHIR provider for patients with the provided
        identifiers
      tags: [patient, search]
      requestBody:
        description: Search patient request
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatientSearchRequest'
              x-body-name: search_details
      responses:
        '200':
          description: Search results
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
    results: List[Dict] = controller.patient_search(search_details=search_details)
    return jsonify(results)
