import click
from flask import Flask
from flask_batteries_included.helpers.apispec import generate_openapi_spec

from dhos_fuego_api.blueprint_api import fuego_blueprint
from dhos_fuego_api.blueprint_development import development_blueprint
from dhos_fuego_api.models.api_spec import dhos_fuego_api_spec


def add_cli_command(app: Flask) -> None:
    @app.cli.command("create-openapi")
    @click.argument("output", type=click.Path())
    def create_api(output: str) -> None:
        generate_openapi_spec(
            dhos_fuego_api_spec, output, fuego_blueprint, development_blueprint
        )
