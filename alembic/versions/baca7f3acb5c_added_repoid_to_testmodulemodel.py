"""added repoId to TestModuleModel

Revision ID: baca7f3acb5c
Revises: b4b0ffad026d
Create Date: 2024-04-30 23:27:30.931847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'baca7f3acb5c'
down_revision: Union[str, None] = 'b4b0ffad026d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('nodes', sa.Column('repo_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'nodes', 'repo_config', ['repo_id'], ['id'])
    op.add_column('test_modules', sa.Column('repo_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'test_modules', 'repo_config', ['repo_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'test_modules', type_='foreignkey')
    op.drop_column('test_modules', 'repo_id')
    op.drop_constraint(None, 'nodes', type_='foreignkey')
    op.drop_column('nodes', 'repo_id')
    # ### end Alembic commands ###
