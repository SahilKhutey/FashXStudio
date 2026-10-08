"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-15 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users table
    op.create_table(
        'users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 2. User Consents table
    op.create_table(
        'user_consents',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('body_photo_processing', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('measurement_extraction', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('camera_stream_access', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('personalization_profiling', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('ml_model_training', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('third_party_analytics', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 3. Canonical Garments table
    op.create_table(
        'canonical_garments',
        sa.Column('canonical_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('subcategory', sa.String(50), nullable=False),
        sa.Column('gender_target', sa.String(20), nullable=False),
        sa.Column('silhouette', sa.String(50), nullable=False),
        sa.Column('primary_color', sa.String(50), nullable=False),
        sa.Column('color_hex', sa.String(7), nullable=False),
        sa.Column('color_palette_type', sa.String(50), nullable=False),
        sa.Column('material', sa.String(100), nullable=False),
        sa.Column('formality_level', sa.String(50), server_default='casual', nullable=False),
        sa.Column('enrichment_confidence', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('garment_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_canonical_garments_category', 'canonical_garments', ['category', 'subcategory'])

    # 4. Try-On Jobs table
    op.create_table(
        'tryon_jobs',
        sa.Column('job_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('canonical_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('canonical_garments.canonical_id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_photo_id', sa.String(64), nullable=False),
        sa.Column('status', sa.String(30), server_default='queued', nullable=False),
        sa.Column('cache_key', sa.String(64), nullable=False),
        sa.Column('result_image_url', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('worker_id', sa.String(64), nullable=True),
        sa.Column('queue_wait_ms', sa.Integer(), nullable=True),
        sa.Column('inference_duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_tryon_jobs_cache_key', 'tryon_jobs', ['cache_key'])
    op.create_index('idx_tryon_jobs_user_status', 'tryon_jobs', ['user_id', 'status'])


def downgrade() -> None:
    op.drop_table('tryon_jobs')
    op.drop_table('canonical_garments')
    op.drop_table('user_consents')
    op.drop_table('users')
