"""Added chatroom table

Revision ID: 9b302200ddb2
Revises: 8c5ad72da78c
Create Date: 2021-11-16 23:38:35.692459

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b302200ddb2'
down_revision = '8c5ad72da78c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chat_rooms',
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('modified_at', sa.DateTime(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('chatroom_members_association',
    sa.Column('room_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('member_type', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['room_id'], ['chat_rooms.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_chatroom_members_association_room_id'), 'chatroom_members_association', ['room_id'], unique=False)
    op.create_index(op.f('ix_chatroom_members_association_user_id'), 'chatroom_members_association', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_chatroom_members_association_user_id'), table_name='chatroom_members_association')
    op.drop_index(op.f('ix_chatroom_members_association_room_id'), table_name='chatroom_members_association')
    op.drop_table('chatroom_members_association')
    op.drop_table('chat_rooms')
    # ### end Alembic commands ###