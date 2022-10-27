import logging

from ..common.lf_share_revoke import LFShareRevoke
from ....db import models

log = logging.getLogger(__name__)


class SameAccountShareRevoke(LFShareRevoke):
    def __init__(
        self,
        session,
        shared_db_name: str,
        dataset: models.Dataset,
        share: models.ShareObject,
        shared_tables: [models.DatasetTable],
        source_environment: models.Environment,
        target_environment: models.Environment,
        env_group: models.EnvironmentGroup,
    ):
        super().__init__(
            session,
            shared_db_name,
            dataset,
            share,
            shared_tables,
            source_environment,
            target_environment,
            env_group,
        )

    def revoke_share(self) -> bool:
        """
        Revokes a share on same account
        1) revoke resource link access
        2) revoke source table access
        3) delete shared database
        Returns
        -------
        True if revoke is successful
        """

        self.revoke_shared_tables_access()

        self.delete_shared_database()

        return True
