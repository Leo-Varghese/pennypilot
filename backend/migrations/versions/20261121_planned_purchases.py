"""planned purchases"""
from alembic import op
import sqlalchemy as sa

revision = "20261121_planned"
down_revision = "20261119_bank_import"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "planned_purchases",
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("planned_amount", sa.Numeric(20, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("category_id", sa.String(36), nullable=True),
        sa.Column("merchant", sa.String(160), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("transaction_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.CheckConstraint("planned_amount > 0", name="positive_planned_purchase_amount"),
        sa.CheckConstraint("priority BETWEEN 1 AND 3", name="planned_purchase_priority"),
        sa.CheckConstraint("status IN ('planned','purchased','cancelled')", name="planned_purchase_status"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_id"),
    )
    op.create_index("ix_planned_purchases_category_id", "planned_purchases", ["category_id"])
    op.create_index("ix_planned_purchases_status", "planned_purchases", ["status"])
    op.create_index("ix_planned_purchases_user_id", "planned_purchases", ["user_id"])
    op.create_index("ix_planned_purchase_owner_status", "planned_purchases", ["user_id", "status"])


def downgrade():
    op.drop_index("ix_planned_purchase_owner_status", table_name="planned_purchases")
    op.drop_index("ix_planned_purchases_user_id", table_name="planned_purchases")
    op.drop_index("ix_planned_purchases_status", table_name="planned_purchases")
    op.drop_index("ix_planned_purchases_category_id", table_name="planned_purchases")
    op.drop_table("planned_purchases")