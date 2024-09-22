"""empty message

Revision ID: bae24e4db269
Revises: c9ac6c4ed890
Create Date: 2024-09-13 11:38:09.930501

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bae24e4db269'
down_revision = 'c9ac6c4ed890'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('review-lessons', schema=None) as batch_op:
        batch_op.drop_column('lesson_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('review-lessons', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lesson_id', sa.VARCHAR(), nullable=False))

    # ### end Alembic commands ###
