"""init_casbin_table_and_data

Revision ID: ff6357189a84
Revises: d0d6403df0d7
Create Date: 2026-04-29 19:20:40.626755

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import column, table


# revision identifiers, used by Alembic.
revision = "ff6357189a84"
down_revision = "d0d6403df0d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "casbin_rule",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ptype", sa.String(length=255), nullable=True, default=None),
        sa.Column("v0", sa.String(length=255), nullable=True, default=None),
        sa.Column("v1", sa.String(length=255), nullable=True, default=None),
        sa.Column("v2", sa.String(length=255), nullable=True, default=None),
        sa.Column("v3", sa.String(length=255), nullable=True, default=None),
        sa.Column("v4", sa.String(length=255), nullable=True, default=None),
        sa.Column("v5", sa.String(length=255), nullable=True, default=None),
    )
    op.create_index("ix_casbin_rule_ptype_v0_v1", "casbin_rule", ["ptype", "v0", "v1"])

    casbin_rule = table(
        "casbin_rule",
        column("ptype", sa.String),
        column("v0", sa.String),
        column("v1", sa.String),
        column("v2", sa.String),
        column("v3", sa.String),
        column("v4", sa.String),
        column("v5", sa.String),
    )

    op.bulk_insert(
        casbin_rule,
        [
            {
                "ptype": "g",
                "v0": "user:1",
                "v1": "role:admin",
                "v2": None,
                "v3": None,
                "v4": None,
                "v5": None,
            },
            {
                "ptype": "p",
                "v0": "role:admin",
                "v1": "*",
                "v2": "*",
                "v3": None,
                "v4": None,
                "v5": None,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("casbin_rule")
    pass
