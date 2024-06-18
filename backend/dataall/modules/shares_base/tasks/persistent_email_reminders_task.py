import logging
import os
import sys
from dataall.modules.dataset_sharing.api.types import ShareObject
from dataall.modules.shares_base.services.sharing_service import SharingService
from dataall.base.db import get_engine
from dataall.base.aws.sqs import SqsQueue
from dataall.core.tasks.service_handlers import Worker

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)
Worker.queue = SqsQueue.send


def persistent_email_reminders(engine, envname):
    """
    A method used by the scheduled ECS Task to run persistent_email_reminder() process against ALL
    active share objects within data.all and send emails to all pending shares.
    """
    with engine.scoped_session() as session:
        log.info('Running Persistent Email Reminders Task')
        pending_shares = SharingService.fetch_pending_shares(engine=engine)
        log.info(f'Found {len(pending_shares)} pending shares')
        pending_share: ShareObject
        for pending_share in pending_shares:
            log.info(f'Sending Email Reminder for Share: {pending_share.shareUri}')
            SharingService.persistent_email_reminder(uri=pending_share.shareUri, envname=envname)
        log.info('Completed Persistent Email Reminders Task')


if __name__ == '__main__':
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    persistent_email_reminders(engine=ENGINE, envname=ENVNAME)
