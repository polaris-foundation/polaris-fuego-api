from typing import Tuple

from flask import Flask, Response
from flask_batteries_included.helpers.error_handler import _catch
from she_logging import logger


class FhirException(Exception):
    pass


class FhirServerUnavailableException(Exception):
    pass


def catch_fhir_exception(error: FhirException) -> Tuple[Response, int]:
    return _catch(error=error, log_method=logger.critical, code=500)


def catch_fhir_server_unavailable_exception(
    error: FhirServerUnavailableException,
) -> Tuple[Response, int]:
    return _catch(error=error, log_method=logger.critical, code=503)


def init_fhir_error_handler(app: Flask) -> None:
    app.errorhandler(FhirException)(catch_fhir_exception)
    app.errorhandler(FhirServerUnavailableException)(
        catch_fhir_server_unavailable_exception
    )
