from pathlib import Path

import pytest
import yaml
from flask import Flask
from flask_batteries_included import init_metrics, init_monitoring
from flask_batteries_included.helpers.apispec import generate_openapi_spec

from dhos_fuego_api.app import create_app
from dhos_fuego_api.blueprint_api import fuego_blueprint
from dhos_fuego_api.blueprint_development import development_blueprint
from dhos_fuego_api.models.api_spec import dhos_fuego_api_spec


# Can't use the session app fixture because Flask doesn't like adding blueprints to an app that has handled requests.
@pytest.fixture
def app() -> Flask:
    return create_app(testing=True)


@pytest.mark.usefixtures("app")
def test_openapi(tmp_path: str, app: Flask) -> None:
    """Does the API spec in the blueprint match the one in openapi/openapi.yaml ?"""
    # Add the metrics paths to the app
    init_monitoring(app)
    init_metrics(app)
    new_spec_path = Path(tmp_path) / "testapi.yaml"

    generate_openapi_spec(
        dhos_fuego_api_spec, new_spec_path, fuego_blueprint, development_blueprint
    )

    new_spec = yaml.safe_load(new_spec_path.read_bytes())
    existing_spec = Path(__file__).parent.parent / "dhos_fuego_api/openapi/openapi.yaml"
    existing = yaml.safe_load(existing_spec.read_bytes())

    assert existing == new_spec
