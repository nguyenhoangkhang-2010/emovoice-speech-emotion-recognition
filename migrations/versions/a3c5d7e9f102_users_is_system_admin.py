"""users is_system_admin

Revision ID: a3c5d7e9f102
Revises: 71b8ac410844
Create Date: 2026-11-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3c5d7e9f102'
down_revision: Union[str, Sequence[str], None] = '71b8ac410844'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Thêm cờ quản trị viên hệ thống; tài khoản admin được tạo đầu tiên (admin gốc từ .env) trở thành admin hệ thống."""
    op.add_column('users', sa.Column('is_system_admin', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.get_bind().execute(
        sa.text("UPDATE users SET is_system_admin = :yes WHERE user_id = (SELECT MIN(user_id) FROM users WHERE role = 'Admin')"),
        {"yes": True},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'is_system_admin')
