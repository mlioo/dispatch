"""Adds column for conference challenge

Revision ID: 5d4dee3e24fc
Revises: 8b67c774279d
Create Date: 2020-03-27 10:47:57.672426

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5d4dee3e24fc"
down_revision = "8b67c774279d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "conference",
        sa.Column("conference_challenge", sa.String(), server_default="N/A", nullable=False),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("conference", "conference_challenge")
    # ### end Alembic commands ###
