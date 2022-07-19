"""nullable request details

Revision ID: 7303d767d7ad
Revises: 9e78cb8974a7
Create Date: 2021-01-29 13:04:33.647895

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7303d767d7ad"
down_revision = "9e78cb8974a7"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "fhir_request",
        "request_body",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    )
    op.alter_column(
        "fhir_request",
        "response_body",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    )


def downgrade():
    op.alter_column(
        "fhir_request",
        "response_body",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    )
    op.alter_column(
        "fhir_request",
        "request_body",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    )
