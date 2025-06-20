"""Add VM metrics table

Revision ID: 001_add_vm_metrics
Revises: 
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_vm_metrics'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add VM metrics table."""
    # Create vm_metrics table
    op.create_table('vm_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vm_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_unit', sa.String(length=20), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['vm_id'], ['virtual_machines.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_vm_metrics_lookup', 'vm_metrics', ['vm_id', 'timestamp'])
    op.create_index('idx_vm_metrics_timestamp', 'vm_metrics', ['vm_id', 'metric_name', 'timestamp'])
    op.create_index(op.f('ix_vm_metrics_id'), 'vm_metrics', ['id'])
    op.create_index(op.f('ix_vm_metrics_metric_name'), 'vm_metrics', ['metric_name'])


def downgrade():
    """Remove VM metrics table."""
    op.drop_index(op.f('ix_vm_metrics_metric_name'), table_name='vm_metrics')
    op.drop_index(op.f('ix_vm_metrics_id'), table_name='vm_metrics')
    op.drop_index('idx_vm_metrics_timestamp', table_name='vm_metrics')
    op.drop_index('idx_vm_metrics_lookup', table_name='vm_metrics')
    op.drop_table('vm_metrics')