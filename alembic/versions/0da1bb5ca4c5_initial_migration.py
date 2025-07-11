"""initial migration

Revision ID: 0da1bb5ca4c5
Revises: 
Create Date: 2025-07-11 18:39:49.464634

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0da1bb5ca4c5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('oneclick_inscriptions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('username', sa.String(length=256), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=True),
    sa.Column('tbk_user', sa.Text(), nullable=False),
    sa.Column('card_type', sa.String(length=50), nullable=True),
    sa.Column('card_number_masked', sa.String(length=20), nullable=True),
    sa.Column('authorization_code', sa.String(length=20), nullable=True),
    sa.Column('inscription_date', sa.DateTime(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='transbankoneclick'
    )
    op.create_index(op.f('ix_transbankoneclick_oneclick_inscriptions_username'), 'oneclick_inscriptions', ['username'], unique=False, schema='transbankoneclick')
    op.create_table('oneclick_transactions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('username', sa.String(length=256), nullable=False),
    sa.Column('inscription_id', sa.String(length=36), nullable=False),
    sa.Column('parent_buy_order', sa.String(length=255), nullable=False),
    sa.Column('session_id', sa.String(length=255), nullable=True),
    sa.Column('transaction_date', sa.DateTime(), nullable=False),
    sa.Column('accounting_date', sa.String(length=10), nullable=True),
    sa.Column('total_amount', sa.Integer(), nullable=False),
    sa.Column('card_number_masked', sa.String(length=20), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('raw_response', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['inscription_id'], ['transbankoneclick.oneclick_inscriptions.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='transbankoneclick'
    )
    op.create_index(op.f('ix_transbankoneclick_oneclick_transactions_parent_buy_order'), 'oneclick_transactions', ['parent_buy_order'], unique=True, schema='transbankoneclick')
    op.create_index(op.f('ix_transbankoneclick_oneclick_transactions_username'), 'oneclick_transactions', ['username'], unique=False, schema='transbankoneclick')
    op.create_table('oneclick_transaction_details',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('transaction_id', sa.String(length=36), nullable=False),
    sa.Column('commerce_code', sa.String(length=20), nullable=False),
    sa.Column('buy_order', sa.String(length=255), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('authorization_code', sa.String(length=20), nullable=True),
    sa.Column('payment_type_code', sa.String(length=5), nullable=True),
    sa.Column('response_code', sa.Integer(), nullable=False),
    sa.Column('installments_number', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('balance', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['transaction_id'], ['transbankoneclick.oneclick_transactions.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='transbankoneclick'
    )
    op.create_index(op.f('ix_transbankoneclick_oneclick_transaction_details_transaction_id'), 'oneclick_transaction_details', ['transaction_id'], unique=False, schema='transbankoneclick')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_transbankoneclick_oneclick_transaction_details_transaction_id'), table_name='oneclick_transaction_details', schema='transbankoneclick')
    op.drop_table('oneclick_transaction_details', schema='transbankoneclick')
    op.drop_index(op.f('ix_transbankoneclick_oneclick_transactions_username'), table_name='oneclick_transactions', schema='transbankoneclick')
    op.drop_index(op.f('ix_transbankoneclick_oneclick_transactions_parent_buy_order'), table_name='oneclick_transactions', schema='transbankoneclick')
    op.drop_table('oneclick_transactions', schema='transbankoneclick')
    op.drop_index(op.f('ix_transbankoneclick_oneclick_inscriptions_username'), table_name='oneclick_inscriptions', schema='transbankoneclick')
    op.drop_table('oneclick_inscriptions', schema='transbankoneclick')
    # ### end Alembic commands ###