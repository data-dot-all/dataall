"""add_ses_notifications

Revision ID: b3f48fad4693
Revises: 917b923f74bd
Create Date: 2023-10-19 10:57:47.270915

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b3f48fad4693'
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
