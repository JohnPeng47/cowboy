"""added cascade delete from repo to tms and nodes

Revision ID: df1d20e2c832
Revises: 91a43f59cf7d
Create Date: 2024-04-30 23:53:52.137184

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df1d20e2c832'
down_revision: Union[str, None] = '91a43f59cf7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
