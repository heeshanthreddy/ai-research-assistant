"""Add chunks table and NLP fields on papers

Revision ID: c41d9e7a2b10
Revises: a3c9daaabe12
Create Date: 2026-08-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c41d9e7a2b10'
down_revision = 'a3c9daaabe12'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('papers', sa.Column('num_pages', sa.Integer(), nullable=True))
    op.add_column('papers', sa.Column('extraction_method', sa.String(length=50), nullable=True))
    op.add_column('papers', sa.Column('processing_warnings', sa.Text(), nullable=True))

    op.create_table('chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paper_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('page_start', sa.Integer(), nullable=True),
        sa.Column('page_end', sa.Integer(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False),
        sa.Column('embedding', sa.LargeBinary(), nullable=True),
        sa.Column('embedding_backend', sa.String(length=150), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chunks_paper_id'), 'chunks', ['paper_id'], unique=False)
    op.create_index(op.f('ix_chunks_project_id'), 'chunks', ['project_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_chunks_project_id'), table_name='chunks')
    op.drop_index(op.f('ix_chunks_paper_id'), table_name='chunks')
    op.drop_table('chunks')
    op.drop_column('papers', 'processing_warnings')
    op.drop_column('papers', 'extraction_method')
    op.drop_column('papers', 'num_pages')
