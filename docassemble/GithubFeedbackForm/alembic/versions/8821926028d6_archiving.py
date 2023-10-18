"""archiving

Revision ID: 8821926028d6
Revises: 542797f969ea
Create Date: 2023-10-18 11:45:07.370329

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '8821926028d6'
down_revision = '542797f969ea'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("feedback_session", sa.Column("archived", sa.Boolean))
    op.add_column("feedback_session", sa.Column("datetime", sa.TIMESTAMP(timezone=True), server_default=datetime.min))


def downgrade() -> None:
    op.drop_column("feedback_session", "archived")
    op.drop_column("feedback_session", "datetime")
