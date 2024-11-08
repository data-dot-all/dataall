import logging
import os
import sys

from dataall.modules.shares_base.services.sharing_service import SharingService
from dataall.base.db import get_engine
from dataall.base.loader import load_modules, ImportMode

root = logging.getLogger()
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)
log.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


if __name__ == '__main__':
    try:
        load_modules(modes={ImportMode.SHARES_TASK})
        ENVNAME = os.environ.get('envname', 'local')
        ENGINE = get_engine(envname=ENVNAME)

        share_uri = os.getenv('shareUri')
        share_item_uri = os.getenv('shareItemUris')
        handler = os.getenv('handler')

        if handler == 'approve_share':
            log.info(f'Starting processing task for share : {share_uri}...')
            SharingService.approve_share(engine=ENGINE, share_uri=share_uri)

        elif handler == 'revoke_share':
            log.info(f'Starting revoking task for share : {share_uri}...')
            SharingService.revoke_share(engine=ENGINE, share_uri=share_uri)

        elif handler == 'verify_share':
            log.info(f'Starting verify task for share : {share_uri}...')
            SharingService.verify_share(engine=ENGINE, share_uri=share_uri)

        elif handler == 'reapply_share':
            log.info(f'Starting re-apply task for share : {share_uri}...')
            SharingService.reapply_share(engine=ENGINE, share_uri=share_uri)

        log.info('Sharing task finished successfully')

    except Exception as e:
        log.error(f'Sharing task failed due to: {e}')
        raise e
