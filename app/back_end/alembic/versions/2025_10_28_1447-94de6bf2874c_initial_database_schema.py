"""Initial database schema

Revision ID: 94de6bf2874c
Revises:
Create Date: 2025-10-28 14:47:54.185022

Creates all tables for KATH genetic analysis platform:
- workspaces: User workspace management
- files: File metadata and hierarchy
- variants: Genetic variant data
- annotations: Analysis tool results (SpliceAI, CADD, REVEL)
- aggregations: Cached aggregation results
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "94de6bf2874c"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workspaces table
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(255), nullable=False, comment="User UUID"),
        sa.Column("name", sa.String(255), nullable=False, comment="Workspace name"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workspaces")),
    )
    op.create_index("ix_workspaces_created_at", "workspaces", ["created_at"], unique=False)

    # Create files table
    op.create_table(
        "files",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False, comment="File name"),
        sa.Column("path", sa.String(512), nullable=False, comment="Relative path within workspace"),
        sa.Column("file_type", sa.String(10), nullable=False, comment="file or folder"),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True, default=0, comment="Number of variant rows"),
        sa.Column("column_count", sa.Integer(), nullable=True, default=0, comment="Number of columns"),
        sa.Column("data_source", sa.String(50), nullable=True, comment="gnomAD, ClinVar, LOVD, Custom"),
        sa.Column("header_json", sa.Text(), nullable=True, comment="JSON array of column names"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], name=op.f("fk_files_workspace_id_workspaces"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["parent_id"], ["files.id"], name=op.f("fk_files_parent_id_files"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_files")),
        sa.UniqueConstraint("workspace_id", "path", name="uq_workspace_path"),
    )
    op.create_index("ix_files_workspace_id", "files", ["workspace_id"], unique=False)
    op.create_index("ix_files_path", "files", ["workspace_id", "path"], unique=False)
    op.create_index("ix_files_parent_id", "files", ["parent_id"], unique=False)
    op.create_index("ix_files_file_type", "files", ["file_type"], unique=False)

    # Create variants table
    op.create_table(
        "variants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False, comment="Original CSV row number"),
        sa.Column("chromosome", sa.String(10), nullable=True, comment="Chromosome"),
        sa.Column("position", sa.Integer(), nullable=True, comment="Genomic position"),
        sa.Column("ref_allele", sa.String(255), nullable=True, comment="Reference allele"),
        sa.Column("alt_allele", sa.String(255), nullable=True, comment="Alternative allele"),
        sa.Column("variant_id", sa.String(255), nullable=True, comment="External variant ID"),
        sa.Column("gen_pos", sa.String(255), nullable=True, comment="chr-pos-ref-alt format"),
        sa.Column("gene", sa.String(255), nullable=True, comment="Gene symbol"),
        sa.Column("transcript", sa.String(255), nullable=True, comment="Transcript ID"),
        sa.Column("consequence", sa.String(255), nullable=True, comment="Variant consequence"),
        sa.Column("data_json", sa.Text(), nullable=True, comment="JSON object for other columns"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], name=op.f("fk_variants_file_id_files"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_variants")),
    )
    op.create_index("ix_variants_file_id", "variants", ["file_id"], unique=False)
    op.create_index("ix_variants_file_row", "variants", ["file_id", "row_index"], unique=False)
    op.create_index(
        "ix_variants_lookup", "variants", ["chromosome", "position", "ref_allele", "alt_allele"], unique=False
    )
    op.create_index("ix_variants_chromosome", "variants", ["chromosome"], unique=False)
    op.create_index("ix_variants_variant_id", "variants", ["variant_id"], unique=False)
    op.create_index("ix_variants_gen_pos", "variants", ["gen_pos"], unique=False)
    op.create_index("ix_variants_gene", "variants", ["gene"], unique=False)

    # Create annotations table
    op.create_table(
        "annotations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(50), nullable=False, comment="Tool name"),
        sa.Column("annotation_type", sa.String(50), nullable=False, comment="Score/annotation type"),
        sa.Column("score_value", sa.Float(), nullable=True, comment="Numeric score"),
        sa.Column("score_label", sa.String(100), nullable=True, comment="Classification label"),
        sa.Column("metadata_json", sa.Text(), nullable=True, comment="Additional tool data"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(
            ["variant_id"], ["variants.id"], name=op.f("fk_annotations_variant_id_variants"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_annotations")),
    )
    op.create_index("ix_annotations_variant_id", "annotations", ["variant_id"], unique=False)
    op.create_index("ix_annotations_tool_name", "annotations", ["tool_name"], unique=False)
    op.create_index("idx_annotations_tool_type", "annotations", ["tool_name", "annotation_type"], unique=False)
    op.create_index("idx_annotations_tool_score", "annotations", ["tool_name", "score_value"], unique=False)

    # Create aggregations table
    op.create_table(
        "aggregations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("column_name", sa.String(255), nullable=False, comment="Column being aggregated"),
        sa.Column("operation", sa.String(10), nullable=False, comment="SUM, AVG, MIN, MAX, COUNT"),
        sa.Column("filter_json", sa.Text(), nullable=True, comment="JSON of applied filters"),
        sa.Column("result_value", sa.Float(), nullable=False, comment="Aggregation result"),
        sa.Column("cached_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("expires_at", sa.DateTime(), nullable=True, comment="Cache expiration"),
        sa.ForeignKeyConstraint(
            ["file_id"], ["files.id"], name=op.f("fk_aggregations_file_id_files"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_aggregations")),
        sa.UniqueConstraint("file_id", "column_name", "operation", "filter_json", name="uq_aggregation_key"),
    )
    op.create_index("ix_aggregations_file_column", "aggregations", ["file_id", "column_name"], unique=False)
    op.create_index("ix_aggregations_expires", "aggregations", ["expires_at"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table("aggregations")
    op.drop_table("annotations")
    op.drop_table("variants")
    op.drop_table("files")
    op.drop_table("workspaces")
