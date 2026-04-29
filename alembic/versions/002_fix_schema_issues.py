"""Fix schema issues: rename extra_metadata -> meta_info, fix order_id types

Revision ID: 002
Revises: 001
Create Date: 2026-04-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename extra_metadata -> meta_info in all tables
    op.alter_column('orders', 'extra_metadata', new_column_name='meta_info',
                    existing_type=postgresql.JSON(astext_type=sa.Text()))
    op.alter_column('decisions', 'extra_metadata', new_column_name='meta_info',
                    existing_type=postgresql.JSON(astext_type=sa.Text()))
    op.alter_column('transactions', 'extra_metadata', new_column_name='meta_info',
                    existing_type=postgresql.JSON(astext_type=sa.Text()))
    op.alter_column('ai_interactions', 'extra_metadata', new_column_name='meta_info',
                    existing_type=postgresql.JSON(astext_type=sa.Text()))

    # Fix foreign keys: drop old fk constraints, change order_id from String to Integer
    # Messages table
    op.drop_constraint('messages_order_id_fkey', 'messages')
    op.alter_column('messages', 'order_id',
                    existing_type=sa.String(length=100),
                    type_=sa.Integer(),
                    postgresql_using='order_id::integer',
                    nullable=False)
    op.create_foreign_key('messages_order_id_fkey', 'messages', 'orders',
                          ['order_id'], ['id'])

    # Decisions table
    op.drop_constraint('decisions_order_id_fkey', 'decisions')
    op.alter_column('decisions', 'order_id',
                    existing_type=sa.String(length=100),
                    type_=sa.Integer(),
                    postgresql_using='order_id::integer',
                    nullable=False)
    op.create_foreign_key('decisions_order_id_fkey', 'decisions', 'orders',
                          ['order_id'], ['id'])

    # Transactions table
    op.drop_constraint('transactions_order_id_fkey', 'transactions')
    op.alter_column('transactions', 'order_id',
                    existing_type=sa.String(length=100),
                    type_=sa.Integer(),
                    postgresql_using='order_id::integer',
                    nullable=False)
    op.create_foreign_key('transactions_order_id_fkey', 'transactions', 'orders',
                          ['order_id'], ['id'])

    # AI Interactions table
    op.alter_column('ai_interactions', 'order_id',
                    existing_type=sa.String(length=100),
                    type_=sa.Integer(),
                    postgresql_using='order_id::integer',
                    nullable=True)


def downgrade() -> None:
    # Revert AI Interactions
    op.alter_column('ai_interactions', 'order_id',
                    existing_type=sa.Integer(),
                    type_=sa.String(length=100),
                    nullable=True)

    # Revert Transactions
    op.drop_constraint('transactions_order_id_fkey', 'transactions')
    op.alter_column('transactions', 'order_id',
                    existing_type=sa.Integer(),
                    type_=sa.String(length=100),
                    nullable=False)
    op.create_foreign_key('transactions_order_id_fkey', 'transactions', 'orders',
                          ['order_id'], ['order_id'])

    # Revert Decisions
    op.drop_constraint('decisions_order_id_fkey', 'decisions')
    op.alter_column('decisions', 'order_id',
                    existing_type=sa.Integer(),
                    type_=sa.String(length=100),
                    nullable=False)
    op.create_foreign_key('decisions_order_id_fkey', 'decisions', 'orders',
                          ['order_id'], ['order_id'])

    # Revert Messages
    op.drop_constraint('messages_order_id_fkey', 'messages')
    op.alter_column('messages', 'order_id',
                    existing_type=sa.Integer(),
                    type_=sa.String(length=100),
                    nullable=False)
    op.create_foreign_key('messages_order_id_fkey', 'messages', 'orders',
                          ['order_id'], ['order_id'])

    # Rename meta_info -> extra_metadata
    op.alter_column('ai_interactions', 'meta_info', new_column_name='extra_metadata',
                    existing_type=postgresql.JSON(astext_type=sa.Text()))
    op.alter_column('transactions', 'meta_info', new_column_name='extra_metadata',
                    existing_type=postgresql.JSON(astext_type=sa.Text()))
    op.alter_column('decisions', 'meta_info', new_column_name='extra_metadata',
                    existing_type=postgresql.JSON(astext_type=sa.Text()))
    op.alter_column('orders', 'meta_info', new_column_name='extra_metadata',
                    existing_type=postgresql.JSON(astext_type=sa.Text()))
