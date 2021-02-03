"""Changing table name

Revision ID: 56273a149fc6
Revises: d77d491a30f9
Create Date: 2021-01-28 13:16:05.208769

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '56273a149fc6'
down_revision = 'd77d491a30f9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('agent__profile',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('a_name', sa.String(length=64), nullable=True),
    sa.Column('a_user', sa.String(length=64), nullable=True),
    sa.Column('a_pass', sa.String(length=64), nullable=True),
    sa.Column('a_serial', sa.String(length=64), nullable=True),
    sa.Column('a_access', sa.String(length=64), nullable=True),
    sa.Column('a_env', sa.String(length=250), nullable=True),
    sa.Column('a_ipaddr', sa.String(length=32), nullable=True),
    sa.Column('a_location', sa.String(length=64), nullable=True),
    sa.Column('a_command_line', sa.String(length=32), nullable=True),
    sa.Column('a_duration', sa.Integer(), nullable=True),
    sa.Column('a_owner', sa.String(length=64), nullable=True),
    sa.Column('a_last_reserved', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('a_name')
    )
    op.create_index(op.f('ix_agent__profile_a_last_reserved'), 'agent__profile', ['a_last_reserved'], unique=False)
    op.drop_index('a_name', table_name='agent_profile')
    op.drop_index('ix_agent_profile_a_last_reserved', table_name='agent_profile')
    op.drop_table('agent_profile')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('agent_profile',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('a_name', mysql.VARCHAR(collation='utf8_bin', length=64), nullable=True),
    sa.Column('a_user', mysql.VARCHAR(collation='utf8_bin', length=64), nullable=True),
    sa.Column('a_pass', mysql.VARCHAR(collation='utf8_bin', length=64), nullable=True),
    sa.Column('a_serial', mysql.VARCHAR(collation='utf8_bin', length=64), nullable=True),
    sa.Column('a_access', mysql.VARCHAR(collation='utf8_bin', length=64), nullable=True),
    sa.Column('a_env', mysql.VARCHAR(collation='utf8_bin', length=250), nullable=True),
    sa.Column('a_ipaddr', mysql.VARCHAR(collation='utf8_bin', length=32), nullable=True),
    sa.Column('a_location', mysql.VARCHAR(collation='utf8_bin', length=64), nullable=True),
    sa.Column('a_command_line', mysql.VARCHAR(collation='utf8_bin', length=32), nullable=True),
    sa.Column('a_duration', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('a_owner', mysql.VARCHAR(collation='utf8_bin', length=64), nullable=True),
    sa.Column('a_last_reserved', mysql.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8_bin',
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    op.create_index('ix_agent_profile_a_last_reserved', 'agent_profile', ['a_last_reserved'], unique=False)
    op.create_index('a_name', 'agent_profile', ['a_name'], unique=True)
    op.drop_index(op.f('ix_agent__profile_a_last_reserved'), table_name='agent__profile')
    op.drop_table('agent__profile')
    # ### end Alembic commands ###
