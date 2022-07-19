"""fhir request


Revision ID: 9e78cb8974a7
Revises: 
Create Date: 2021-01-21 11:42:48.405585

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9e78cb8974a7"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fhir_request",
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("created_by_", sa.String(), nullable=False),
        sa.Column("modified", sa.DateTime(), nullable=False),
        sa.Column("modified_by_", sa.String(), nullable=False),
        sa.Column("request_url", sa.String(), nullable=False),
        sa.Column(
            "request_body", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "response_body", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.PrimaryKeyConstraint("uuid"),
    )


def downgrade():
    op.drop_table("fhir_request")
