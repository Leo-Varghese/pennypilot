"""password reset tokens"""
from alembic import op
import sqlalchemy as sa
revision = "20261123_password_reset"
down_revision = "20261121_planned"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("password_reset_tokens",
        sa.Column("id",sa.String(36),nullable=False),
        sa.Column("user_id",sa.String(36),nullable=False),
        sa.Column("token_hash",sa.String(64),nullable=False),
        sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("used_at",sa.DateTime(timezone=True),nullable=True),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(["user_id"],["users.id"],ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),sa.UniqueConstraint("token_hash"))
    op.create_index("ix_password_reset_tokens_user_id","password_reset_tokens",["user_id"])
    op.create_index("ix_password_reset_tokens_token_hash","password_reset_tokens",["token_hash"],unique=True)
    op.create_index("ix_password_reset_tokens_expires_at","password_reset_tokens",["expires_at"])

def downgrade():
    op.drop_table("password_reset_tokens")