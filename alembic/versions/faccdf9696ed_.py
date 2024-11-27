"""empty message

Revision ID: faccdf9696ed
Revises: 87a33ce1322a
Create Date: 2024-11-27 15:37:38.654668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'faccdf9696ed'
down_revision: Union[str, None] = '87a33ce1322a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
