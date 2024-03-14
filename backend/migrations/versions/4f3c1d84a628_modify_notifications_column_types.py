"""modify_notifications_column_types

Revision ID: 4f3c1d84a628
Revises: 917b923f74bd
Create Date: 2023-10-20 15:04:15.061516

"""

import os

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f3c1d84a628'
down_revision = '917b923f74bd'
branch_labels = None
depends_on = None


def upgrade():
    """
    Define column "type" as: type = Column(String, nullable=True)
    Rename column " " to " " both of type String
    """
    envname = os.getenv('envname', 'local')
    op.execute(f'ALTER TABLE {envname}.notification ALTER COLUMN "type" TYPE VARCHAR(100);')  # nosemgrep
    # semgrep finding ignored as no upstream user input is passed to the statement function
    # Only code admins will have access to the envname parameter of the f-string

    op.alter_column('notification', 'username', new_column_name='recipient', nullable=False, existing_type=sa.String())
    print('Notification columns updated')


def downgrade():
    """
    Revert back column type to
    type = Column(Enum(NotificationType), nullable=True)
    and column name to username
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
        nullable=True,
    )
    op.alter_column('notification', 'recipient', new_column_name='username', nullable=False, existing_type=sa.String())
