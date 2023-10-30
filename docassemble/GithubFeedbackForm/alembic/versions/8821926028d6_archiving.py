"""archiving

Revision ID: 8821926028d6
Revises: 542797f969ea
Create Date: 2023-10-18 11:45:07.370329

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection
from datetime import datetime

# revision identifiers, used by Alembic.
revision = "8821926028d6"
down_revision = "542797f969ea"
branch_labels = None
depends_on = None


# Code based on https://github.com/talkpython/data-driven-web-apps-with-flask
def table_has_column(table, column, engine=None):
    config = op.get_context().config
    if not engine:
        engine = sa.engine_from_config(
            config.get_section(config.config_ini_section), prefix='sqlalchemy.')
    insp = sa.inspect(engine)
    has_column = False
    for col in insp.get_columns(table):
        if column not in col['name']:
            continue
        has_column = True
    return has_column


def upgrade() -> None:
    config = op.get_context().config
    engine = sa.engine_from_config(
        config.get_section(config.config_ini_section), prefix='sqlalchemy.')
    make_archived = not table_has_column("feedback_session", "archived", engine)
    make_datetime = not table_has_column("feedback_session", "datetime", engine)
    if make_archived:
        op.add_column(
            "feedback_session",
            sa.Column("archived", sa.Boolean, server_default="False"),
        )
    if make_datetime:
        op.add_column(
            "feedback_session",
            sa.Column(
                "datetime",
                sa.TIMESTAMP(timezone=True),
                server_default=str(datetime.min),
            ),
        )


def downgrade() -> None:
    op.drop_column("feedback_session", "archived")
    op.drop_column("feedback_session", "datetime")
