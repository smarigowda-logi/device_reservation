"""add constraint

Revision ID: a4df8dbf9373
Revises: 9ab444e9ba23
Create Date: 2021-01-22 16:24:53.610380

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a4df8dbf9373'
down_revision = '9ab444e9ba23'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('reservation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('agent', sa.String(length=32), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.Column('r_user', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('r_user', 'agent', name='unique_agent_user')
    )
    op.create_index(op.f('ix_reservation_timestamp'), 'reservation', ['timestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_reservation_timestamp'), table_name='reservation')
    op.drop_table('reservation')
    # ### end Alembic commands ###