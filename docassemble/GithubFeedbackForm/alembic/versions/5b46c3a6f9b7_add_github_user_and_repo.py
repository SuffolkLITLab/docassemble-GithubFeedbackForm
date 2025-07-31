"""add github user and repo

Revision ID: 5b46c3a6f9b7
Revises: 8821926028d6
Create Date: 2025-07-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5b46c3a6f9b7'
down_revision = '8821926028d6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('feedback_session', sa.Column('github_user', sa.String(), nullable=True))
    op.add_column('feedback_session', sa.Column('github_repo_name', sa.String(), nullable=True))


def downgrade():
    op.drop_column('feedback_session', 'github_user')
    op.drop_column('feedback_session', 'github_repo_name')
