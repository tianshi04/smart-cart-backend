"""Implement checkout flow and remove smartcart

Revision ID: abb41021d4e4
Revises: fd504dbc1c8a
Create Date: 2025-08-30 22:54:14.508759

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'abb41021d4e4'
down_revision: Union[str, Sequence[str], None] = 'fd504dbc1c8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Drop foreign key constraint
    op.drop_constraint(
        'shopping_sessions_smart_cart_id_fkey',
        'shopping_sessions',
        type_='foreignkey'
    )

    # 2. Drop column smart_cart_id
    with op.batch_alter_table('shopping_sessions') as batch_op:
        batch_op.drop_column('smart_cart_id')

    # 3. Drop table smart_carts
    op.drop_table('smart_carts')

def downgrade() -> None:
    """Downgrade schema."""
    # 1. Tạo lại table smart_carts trước
    op.create_table(
        'smart_carts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('hardware_id', sa.VARCHAR(length=100), nullable=True),
        sa.Column('status', sa.VARCHAR(length=50), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('smart_carts_pkey')),
        sa.UniqueConstraint('hardware_id', name=op.f('smart_carts_hardware_id_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )

    # 2. Thêm column smart_cart_id vào shopping_sessions
    with op.batch_alter_table('shopping_sessions') as batch_op:
        batch_op.add_column(sa.Column('smart_cart_id', sa.UUID(), nullable=True))  # để tạm nullable

    # 3. Tạo foreign key constraint
    op.create_foreign_key(
        op.f('shopping_sessions_smart_cart_id_fkey'),
        'shopping_sessions',
        'smart_carts',
        ['smart_cart_id'],
        ['id']
    )
