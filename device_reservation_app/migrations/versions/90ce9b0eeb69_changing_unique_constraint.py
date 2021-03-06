"""changing unique constraint

Revision ID: 90ce9b0eeb69
Revises: a11bd4d605dd
Create Date: 2021-01-22 12:27:56.972491

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '90ce9b0eeb69'
down_revision = 'a11bd4d605dd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'reservation', type_='foreignkey')
    op.drop_column('reservation', 'username')
    op.drop_column('reservation', 'ruser')
    op.drop_column('reservation', 'user_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('reservation', sa.Column('user_id', sa.INTEGER(), nullable=True))
    op.add_column('reservation', sa.Column('ruser', sa.VARCHAR(length=64), nullable=True))
    op.add_column('reservation', sa.Column('username', sa.VARCHAR(length=64), nullable=True))
    op.create_foreign_key(None, 'reservation', 'user', ['user_id'], ['id'])
    # ### end Alembic commands ###
