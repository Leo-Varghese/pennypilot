"""bank statement import batches"""
from alembic import op
import sqlalchemy as sa

revision = "20261119_bank_import"
down_revision = "b9c5c129a30d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bank_import_batches",
        sa.Column("account_id", sa.String(36), nullable=False),
        sa.Column("source_bank", sa.String(100), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_digest", sa.String(64), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "account_id", "file_digest", name="uq_bank_import_file"),
    )
    op.create_index("ix_bank_import_batches_account_id", "bank_import_batches", ["account_id"])
    op.create_index("ix_bank_import_batches_user_id", "bank_import_batches", ["user_id"])

    op.create_table(
        "bank_import_items",
        sa.Column("batch_id", sa.String(36), nullable=False),
        sa.Column("transaction_id", sa.String(36), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("original_description", sa.Text(), nullable=False),
        sa.Column("bank_reference", sa.String(160), nullable=False),
        sa.Column("statement_date", sa.Date(), nullable=False),
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["bank_import_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_id"),
        sa.UniqueConstraint("user_id", "fingerprint", name="uq_bank_import_fingerprint"),
    )
    op.create_index("ix_bank_import_items_batch_id", "bank_import_items", ["batch_id"])
    op.create_index("ix_bank_import_items_fingerprint", "bank_import_items", ["fingerprint"])
    op.create_index("ix_bank_import_items_user_id", "bank_import_items", ["user_id"])


def downgrade():
    op.drop_index("ix_bank_import_items_user_id", table_name="bank_import_items")
    op.drop_index("ix_bank_import_items_fingerprint", table_name="bank_import_items")
    op.drop_index("ix_bank_import_items_batch_id", table_name="bank_import_items")
    op.drop_table("bank_import_items")
    op.drop_index("ix_bank_import_batches_user_id", table_name="bank_import_batches")
    op.drop_index("ix_bank_import_batches_account_id", table_name="bank_import_batches")
    op.drop_table("bank_import_batches")