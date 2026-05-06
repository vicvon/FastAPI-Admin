"""seed default admin and permissions

Revision ID: d0d6403df0d7
Revises: 44dbcfaa6706
Create Date: 2026-04-22 11:24:29.999737

"""
from alembic import op
from pathlib import Path

# revision identifiers, used by Alembic.
revision = 'd0d6403df0d7'
down_revision = '21f977a1e758'
branch_labels = None
depends_on = None


def upgrade() -> None:
    base_dir = Path(__file__).resolve().parent
    op.execute((base_dir / "init_user_data.sql").read_text(encoding="utf-8"))
    op.execute((base_dir / "init_permissions.sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    base_dir = Path(__file__).resolve().parent
    op.execute((base_dir / "uninit_permissions.sql").read_text(encoding="utf-8"))
    op.execute((base_dir / "uninit_user_data.sql").read_text(encoding="utf-8"))
