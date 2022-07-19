from typing import NoReturn

from flask_batteries_included.sqldb import ModelIdentifier, db
from sqlalchemy.dialects.postgresql import JSONB


class FhirRequest(ModelIdentifier, db.Model):
    request_url = db.Column(db.String, nullable=False, unique=False)
    request_body = db.Column(JSONB, nullable=True, unique=False)
    response_body = db.Column(JSONB, nullable=True, unique=False)

    @staticmethod
    def schema() -> NoReturn:
        raise NotImplemented
