import logging
import os

from .lf_cross_account.approve_share import (
    CrossAccountShareApproval,
)
from .lf_cross_account.revoke_share import (
    CrossAccountShareRevoke,
)
from .lf_same_account.approve_share import (
    SameAccountShareApproval,
)
from .lf_same_account.revoke_share import (
    SameAccountShareRevoke,
)
from .common.s3_approve_share import (
    S3ShareApproval
)
from .common.s3_revoke_share import (
    S3ShareRevoke
)

from ...aws.handlers.lakeformation import LakeFormation
from ...aws.handlers.ram import Ram
from ...aws.handlers.sts import SessionHelper
from ...db import api, models, Engine
from ...utils import Parameter

log = logging.getLogger(__name__)


class DataSharingService:
    def __init__(self):
        pass

    @classmethod
    def approve_share(cls, engine: Engine, share_uri: str) -> bool:
        """
        Share tables
        1) Retrieves share related model objects
        2) Build shared database name (unique db per team for a dataset)
        3) Grants pivot role ALL permissions on dataset db and its tables
        4) Calls sharing approval service

        Share folders
        1) (one time only) manage_bucket_policy - grants permission in the bucket policy
        2) grant_target_role_access_policy
        3) manage_access_point_and_policy
        4) update_dataset_bucket_key_policy
        5) update_share_item_status
        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns
        -------
        True if approve succeeds
        """
        with engine.scoped_session() as session:
            (
                source_env_group,
                env_group,
                dataset,
                share,
                shared_tables,
                shared_folders,
                source_environment,
                target_environment,
            ) = api.ShareObject.get_share_data(session, share_uri, ['Approved'])

        log.info(f'Granting permissions to tables : {shared_tables}')
        log.info(f'Granting permissions to folders : {shared_folders}')

        shared_db_name = cls.build_shared_db_name(dataset, share)

        LakeFormation.grant_pivot_role_all_database_permissions(
            source_environment.AwsAccountId,
            source_environment.region,
            dataset.GlueDatabaseName,
        )

        share_folders_succeed = S3ShareApproval.approve_share(
            session,
            dataset,
            share,
            shared_folders,
            source_environment,
            target_environment,
            source_env_group,
            env_group,
        )

        if source_environment.AwsAccountId != target_environment.AwsAccountId:
            return CrossAccountShareApproval(
                session,
                shared_db_name,
                dataset,
                share,
                shared_tables,
                source_environment,
                target_environment,
                env_group,
            ).approve_share() if share_folders_succeed else False

        return SameAccountShareApproval(
            session,
            shared_db_name,
            dataset,
            share,
            shared_tables,
            source_environment,
            target_environment,
            env_group,
        ).approve_share() if share_folders_succeed else False

    @classmethod
    def reject_share(cls, engine: Engine, share_uri: str):
        """
        1) Retrieves share related model objects
        2) Build shared database name (unique db per team for a dataset)
        3) Grants pivot role ALL permissions on dataset db and its tables
        4) Calls sharing revoke service

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns
        -------
        True if reject succeeds
        """

        with engine.scoped_session() as session:
            (
                source_env_group,
                env_group,
                dataset,
                share,
                shared_tables,
                shared_folders,
                source_environment,
                target_environment,
            ) = api.ShareObject.get_share_data(session, share_uri, ['Rejected'])

            log.info(f'Revoking permissions for tables : {shared_tables}')
            log.info(f'Revoking permissions for folders : {shared_folders}')

            shared_db_name = cls.build_shared_db_name(dataset, share)

            LakeFormation.grant_pivot_role_all_database_permissions(
                source_environment.AwsAccountId,
                source_environment.region,
                dataset.GlueDatabaseName,
            )

            revoke_folders_succeed = S3ShareRevoke.revoke_share(
                session,
                dataset,
                share,
                shared_folders,
                source_environment,
                target_environment,
                source_env_group,
                env_group,
            )

            if source_environment.AwsAccountId != target_environment.AwsAccountId:
                return CrossAccountShareRevoke(
                    session,
                    shared_db_name,
                    dataset,
                    share,
                    shared_tables,
                    source_environment,
                    target_environment,
                    env_group,
                ).revoke_share() if revoke_folders_succeed else False

            return SameAccountShareRevoke(
                session,
                shared_db_name,
                dataset,
                share,
                shared_tables,
                source_environment,
                target_environment,
                env_group,
            ).revoke_share() if revoke_folders_succeed else False

    @classmethod
    def build_shared_db_name(
        cls, dataset: models.Dataset, share: models.ShareObject
    ) -> str:
        """
        Build Glue shared database name.
        Unique per share Uri.
        Parameters
        ----------
        dataset : models.Dataset
        share : models.ShareObject

        Returns
        -------
        Shared database name
        """
        return (dataset.GlueDatabaseName + '_shared_' + share.shareUri)[:254]

    @classmethod
    def clean_lfv1_ram_resources(cls, environment: models.Environment):
        """
        Deletes LFV1 resource shares for an environment
        Parameters
        ----------
        environment : models.Environment

        Returns
        -------
        None
        """
        return Ram.delete_lakeformation_v1_resource_shares(
            SessionHelper.remote_session(accountid=environment.AwsAccountId).client(
                'ram', region_name=environment.region
            )
        )

    @classmethod
    def refresh_shares(cls, engine: Engine) -> bool:
        """
        Refreshes the shares at scheduled frequency
        Also cleans up LFV1 ram resource shares if enabled on SSM
        Parameters
        ----------
        engine : db.engine

        Returns
        -------
        true if refresh succeeds
        """
        with engine.scoped_session() as session:
            environments = session.query(models.Environment).all()
            shares = (
                session.query(models.ShareObject)
                .filter(models.ShareObject.status.in_(['Approved', 'Rejected']))
                .all()
            )

        # Feature toggle: default value is False
        if (
            Parameter().get_parameter(
                os.getenv('envname', 'local'), 'shares/cleanlfv1ram'
            )
            == 'True'
        ):
            log.info('LFV1 Cleanup toggle is enabled')
            for e in environments:
                log.info(
                    f'Cleaning LFV1 ram resource for environment: {e.AwsAccountId}/{e.region}...'
                )
                cls.clean_lfv1_ram_resources(e)

        if not shares:
            log.info('No Approved nor Rejected shares found. Nothing to do...')
            return True

        for share in shares:
            try:
                log.info(
                    f'Refreshing share {share.shareUri} with {share.status} status...'
                )
                if share.status == 'Approved':
                    cls.approve_share(engine, share.shareUri)
                elif share.status == 'Rejected':
                    cls.reject_share(engine, share.shareUri)
            except Exception as e:
                log.error(
                    f'Failed refreshing share {share.shareUri} with {share.status}. '
                    f'due to: {e}'
                )
        return True
