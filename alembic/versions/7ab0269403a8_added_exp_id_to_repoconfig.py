"""added exp_id to RepoConfig

Revision ID: 7ab0269403a8
Revises: 8cbcddf29c9e
Create Date: 2024-05-25 04:32:44.055230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ab0269403a8'
down_revision: Union[str, None] = '8cbcddf29c9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('repo_config', sa.Column('is_experiment', sa.Boolean(), nullable=True))
    op.add_column('test_modules', sa.Column('experiment_id', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('test_modules', 'experiment_id')
    op.drop_column('repo_config', 'is_experiment')
    # ### end Alembic commands ###
