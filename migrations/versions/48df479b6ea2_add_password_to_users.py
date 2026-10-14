"""add_password_to_users

Revision ID: 48df479b6ea2
Revises: 6526bb10876c
Create Date: 2026-10-14 13:42:46.739532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48df479b6ea2'
down_revision: Union[str, Sequence[str], None] = '6526bb10876c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('password', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'password')
