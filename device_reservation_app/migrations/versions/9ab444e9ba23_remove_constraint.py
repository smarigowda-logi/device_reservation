"""remove constraint

Revision ID: 9ab444e9ba23
Revises: 05a6c3b654f1
Create Date: 2021-01-22 16:24:14.111016

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9ab444e9ba23'
down_revision = '05a6c3b654f1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_reservation_timestamp', table_name='reservation')
    op.drop_table('reservation')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('reservation',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('agent', sa.VARCHAR(length=32), nullable=True),
    sa.Column('timestamp', sa.DATETIME(), nullable=True),
    sa.Column('duration', sa.INTEGER(), nullable=True),
    sa.Column('r_user', sa.VARCHAR(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reservation_timestamp', 'reservation', ['timestamp'], unique=False)
    # ### end Alembic commands ###
