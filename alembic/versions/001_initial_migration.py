"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create orders table
    op.create_table('orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.String(length=100), nullable=False),
        sa.Column('ad_id', sa.String(length=100), nullable=True),
        sa.Column('side', sa.String(length=10), nullable=False),
        sa.Column('crypto', sa.String(length=20), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('counterparty', sa.String(length=100), nullable=True),
        sa.Column('counterparty_telegram_id', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_order_id'), 'orders', ['order_id'], unique=True)

    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.String(length=100), nullable=False),
        sa.Column('message_id', sa.String(length=100), nullable=False),
        sa.Column('sender', sa.String(length=20), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(length=50), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('entities', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.order_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id')
    )
    op.create_index(op.f('ix_messages_order_id'), 'messages', ['order_id'], unique=False)

    # Create decisions table
    op.create_table('decisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.String(length=100), nullable=False),
        sa.Column('decision_type', sa.String(length=50), nullable=False),
        sa.Column('approved', sa.Boolean(), nullable=False),
        sa.Column('proposed_action', sa.Text(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('risk_flags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('decided_by', sa.String(length=50), nullable=False),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.order_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_decisions_order_id'), 'decisions', ['order_id'], unique=False)

    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.String(length=100), nullable=False),
        sa.Column('processing_id', sa.String(length=100), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('payment_proof_path', sa.String(length=500), nullable=True),
        sa.Column('payment_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.order_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('processing_id')
    )
    op.create_index(op.f('ix_transactions_order_id'), 'transactions', ['order_id'], unique=False)

    # Create ai_interactions table
    op.create_table('ai_interactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.String(length=100), nullable=True),
        sa.Column('agent_type', sa.String(length=50), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('input_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('output_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_interactions_order_id'), 'ai_interactions', ['order_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_interactions_order_id'), table_name='ai_interactions')
    op.drop_table('ai_interactions')
    op.drop_index(op.f('ix_transactions_order_id'), table_name='transactions')
    op.drop_table('transactions')
    op.drop_index(op.f('ix_decisions_order_id'), table_name='decisions')
    op.drop_table('decisions')
    op.drop_index(op.f('ix_messages_order_id'), table_name='messages')
    op.drop_table('messages')
    op.drop_index(op.f('ix_orders_order_id'), table_name='orders')
    op.drop_table('orders')
