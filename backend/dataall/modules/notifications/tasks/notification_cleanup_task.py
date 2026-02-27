import logging
import os

from dataall.base.db import get_engine
from dataall.base.loader import load_modules, ImportMode
from dataall.modules.notifications.db.notification_repositories import NotificationRepository


log = logging.getLogger(__name__)


def cleanup_old_notifications(engine):
    """
    A method used by the scheduled ECS Task to mark unread notifications older than 90 days as read.
    """
    DAYS_THRESHOLD = 90

    with engine.scoped_session() as session:
        log.info('Running Notification Cleanup Task')

        updated_count = NotificationRepository.mark_old_notifications_as_read(
            session=session, days_threshold=DAYS_THRESHOLD
        )

        if updated_count > 0:
            log.info(f'Successfully cleaned up {updated_count} old notifications')
        else:
            log.info('No old notifications found to clean up')

        log.info('Completed Notification Cleanup Task')


if __name__ == '__main__':
    load_modules(modes={ImportMode.API})
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    cleanup_old_notifications(engine=ENGINE)
