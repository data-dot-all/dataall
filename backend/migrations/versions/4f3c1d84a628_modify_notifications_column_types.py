"""modify_notifications_column_types

Revision ID: 4f3c1d84a628
Revises: 917b923f74bd
Create Date: 2023-10-20 15:04:15.061516

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f3c1d84a628'
down_revision = '917b923f74bd'
branch_labels = None
depends_on = None


def upgrade():
    """
    Define column type as:
    type = Column(String, nullable=True)
    """
    op.alter_column(
        'notification',
        'type',
        existing_type=sa.VARCHAR(),
        nullable=True
    )


def downgrade():
    """
    Revert back column type to
    type = Column(Enum(NotificationType), nullable=True)
    """
    op.alter_column(
        'notification',
        'type',
        existing_type=sa.Enum(
            'SHARE_OBJECT_SUBMITTED',
            'SHARE_ITEM_REQUEST',
            'SHARE_OBJECT_APPROVED',
            'SHARE_OBJECT_REJECTED',
            'SHARE_OBJECT_PENDING_APPROVAL',
            'DATASET_VERSION',
            name='notificationtype',
        ),
        nullable=True
    )
