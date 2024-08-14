import logging
import os
import sys
from datetime import datetime
from dataall.base.loader import load_modules, ImportMode
from dataall.base.db import get_engine
from backend.dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.services.share_notification_service import ShareNotificationService
from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository
from dataall.modules.shares_base.services.sharing_service import SharingService

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


def share_expiration_checker(engine):
    """
    Checks all the share objects which have expiryDate on them and then revokes or notifies users based on if its expired or not
    """
    with engine.scoped_session() as session:
        log.info('Starting share expiration task')
        shares = ShareObjectRepository.get_all_active_shares_with_expiration(session)
        log.info(f'Fetched {len(shares)} active shares with expiration')
        for share in shares:
            if share.expiryDate.date() < datetime.today().date():
                log.info(f'Revoking share with uri: {share.shareUri} as it is expired')
                SharingService.revoke_share(engine=engine, share_uri=share.shareUri)
            else:
                log.info(f'Share with share uri: {share.shareUri} has not yet expired')
                dataset = DatasetBaseRepository.get_dataset_by_uri(session, share.shareUri)
                if share.submittedForExtension:
                    log.info(
                        f'Sending notifications to the owners as share extension requested for share with uri: {share.shareUri}'
                    )
                    ShareNotificationService(
                        session=session, dataset=dataset, share=share
                    ).notify_share_expiration_to_owners()
                else:
                    log.info(
                        f'Sending notifications to the requesters as share extension is not requested for share with uri: {share.shareUri}'
                    )

                    ShareNotificationService(
                        session=session, dataset=dataset, share=share
                    ).notify_share_expiration_to_requesters()


if __name__ == '__main__':
    load_modules(modes={ImportMode.SHARES_TASK})
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    share_expiration_checker(engine=ENGINE)
