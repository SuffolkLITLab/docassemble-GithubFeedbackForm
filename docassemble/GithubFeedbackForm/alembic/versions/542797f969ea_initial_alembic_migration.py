"""initial alembic migration

Revision ID: 542797f969ea
Revises:
Create Date: 2023-10-09 17:06:05.463730

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "542797f969ea"
down_revision = None
branch_labels = None
depends_on = None


# Code based on https://github.com/talkpython/data-driven-web-apps-with-flask
def table_does_not_exist(table, schema=None):
    insp = sa.inspect(op.get_bind())
    return insp.has_table(table, schema) == False


def upgrade() -> None:
    if table_does_not_exist("feedback_session"):
        op.create_table(
            "feedback_session",
            sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
            sa.Column("interview", sa.String, autoincrement=False, nullable=True),
            sa.Column("session_id", sa.String, autoincrement=False, nullable=True),
            sa.Column("body", sa.String, autoincrement=False, nullable=True),
            sa.Column("html_url", sa.String, autoincrement=False, nullable=True),
            sa.PrimaryKeyConstraint("id", name="feedback_session_pkey"),
        )

    if table_does_not_exist("good_or_bad"):
        op.create_table(
            "good_or_bad",
            sa.Column("reaction", sa.INTEGER(), autoincrement=False, nullable=True),
            sa.Column("interview", sa.String, autoincrement=False, nullable=True),
            sa.Column("version", sa.String, autoincrement=False, nullable=True),
            sa.Column(
                "datetime",
                sa.TIMESTAMP(timezone=True),
                autoincrement=False,
                nullable=True,
            ),
        )


def downgrade() -> None:
    op.drop_table("feedback_session")
    op.drop_table("good_or_bad")
