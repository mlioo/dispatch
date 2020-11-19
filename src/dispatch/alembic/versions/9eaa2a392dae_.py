"""Adds executive_report_reminder column to incident priority model

Revision ID: 9eaa2a392dae
Revises: dd3df6a3af3c
Create Date: 2020-05-29 15:06:12.232436

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9eaa2a392dae"
down_revision = "dd3df6a3af3c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "incident_priority", "status_reminder", new_column_name="tactical_report_reminder"
    )
    op.add_column(
        "incident_priority", sa.Column("executive_report_reminder", sa.Integer(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "incident_priority", "tactical_report_reminder", new_column_name="status_reminder"
    )
    op.drop_column("incident_priority", "executive_report_reminder")
    # ### end Alembic commands ###
