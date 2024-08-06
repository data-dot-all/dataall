import logging
import json
from typing import List
from dataall.modules.shares_base.services.sharing_service import ShareData
from dataall.modules.shares_base.services.share_processor_manager import SharesProcessorInterface
from dataall.modules.redshift_datasets_shares.aws.redshift_data import redshift_share_data_client
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftTable
from dataall.modules.redshift_datasets.db.redshift_connection_repositories import RedshiftConnectionRepository

log = logging.getLogger(__name__)


class ProcessRedshiftShare(SharesProcessorInterface):
    def __init__(self, session, share_data, shareable_items, reapply=False):
        self.session = session
        self.share_data: ShareData = share_data
        self.dataset = share_data.dataset
        self.share = share_data.share
        self.tables: List[RedshiftTable] = shareable_items
        self.reapply: bool = reapply

    def process_approved_shares(self) -> bool:
        return True

    def process_revoked_shares(self) -> bool:
        return True

    def verify_shares(self) -> bool:
        return True
