"""Create submission table

Revision ID: 1e02ba21c2f2
Revises: 
Create Date: 2023-03-16 09:01:27.595965

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1e02ba21c2f2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("symbol", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    pass


def downgrade() -> None:
    op.drop_table("submissions")
