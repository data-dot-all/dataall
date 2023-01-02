import logging
import os

from .share_processors.lf_process_cross_account_share import ProcessLFCrossAccountShare
from .share_processors.lf_process_same_account_share import ProcessLFSameAccountShare
from .share_processors.s3_process_share import ProcessS3Share

from ...aws.handlers.ram import Ram
from ...aws.handlers.sts import SessionHelper
from ...db import api, models, Engine
from ...utils import Parameter

log = logging.getLogger(__name__)


class DataSharingService:
    def __init__(self):
        pass

    @classmethod
    def process_share(cls, engine: Engine, share_uri: str) -> bool:
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
                source_environment,
                target_environment,
            ) = api.ShareObject.get_share_data(session, share_uri)

            Share_SM = api.ShareObjectSM(share.status)
            new_share_state = Share_SM.run_transition(models.Enums.ShareObjectActions.Start.value)
            Share_SM.update_state(session, share, new_share_state)

            (
                shared_tables,
                shared_folders
            ) = api.ShareObject.get_share_data_items(session, share_uri, models.ShareItemStatus.Share_Approved.value)

            (
                revoked_tables,
                revoked_folders
            ) = api.ShareObject.get_share_data_items(session, share_uri, models.ShareItemStatus.Revoke_Approved.value)

        log.info(f'Granting permissions to folders : {shared_folders}')

        approved_folders_succeed = ProcessS3Share.process_approved_shares(
            session,
            dataset,
            share,
            shared_folders,
            source_environment,
            target_environment,
            source_env_group,
            env_group
        )
        log.info(f'sharing folders succeeded = {approved_folders_succeed}')

        log.info(f'Revoking permissions to folders : {revoked_folders}')

        revoked_folders_succeed = ProcessS3Share.process_revoked_shares(
            session,
            dataset,
            share,
            revoked_folders,
            source_environment,
            target_environment,
            source_env_group,
            env_group
        )

        log.info(f'revoking folders succeeded = {revoked_folders_succeed}')

        folders_succeed = approved_folders_succeed and revoked_folders_succeed

        if source_environment.AwsAccountId != target_environment.AwsAccountId:
            processor = ProcessLFCrossAccountShare(
                session,
                dataset,
                share,
                shared_tables,
                revoked_tables,
                source_environment,
                target_environment,
                env_group,
            )
        else:
            processor = ProcessLFSameAccountShare(
                session,
                dataset,
                share,
                shared_tables,
                revoked_tables,
                source_environment,
                target_environment,
                env_group
            )

        log.info(f'Granting permissions to tables : {shared_tables}')
        approved_tables_succeed = processor.process_approved_shares()
        log.info(f'sharing tables succeeded = {approved_folders_succeed}')

        log.info(f'Revoking permissions to tables : {revoked_tables}')
        revoked_tables_succeed = processor.process_revoked_shares()
        log.info(f'revoking tables succeeded = {revoked_folders_succeed}')

        tables_succeed = approved_tables_succeed and revoked_tables_succeed

        new_share_state = Share_SM.run_transition(models.Enums.ShareObjectActions.FinishApprove.value)
        Share_SM.update_state(session, share, new_share_state)

        return tables_succeed if folders_succeed else False

    @classmethod
    def revoke_share(cls, engine: Engine, share_uri: str):
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
                source_environment,
                target_environment,
            ) = api.ShareObject.get_share_data(session, share_uri)

            Share_SM = api.ShareObjectSM(share.status)
            new_share_state = Share_SM.run_transition(models.Enums.ShareObjectActions.Start.value)
            Share_SM.update_state(session, share, new_share_state)

            revoked_item_SM = api.ShareItemSM(models.ShareItemStatus.Revoke_Approved.value)
            shared_tables = []
            (
                revoked_tables,
                revoked_folders
            ) = api.ShareObject.get_share_data_items(session, share_uri, revoked_item_SM._state)

            new_state = revoked_item_SM.run_transition(models.ShareObjectActions.Start.value)
            revoked_item_SM.update_state(session, share_uri, new_state)

            log.info(f'Revoking permissions for tables : {revoked_tables}')
            log.info(f'Revoking permissions for folders : {revoked_folders}')

            revoked_folders_succeed = ProcessS3Share.process_revoked_shares(
                session,
                dataset,
                share,
                revoked_folders,
                source_environment,
                target_environment,
                source_env_group,
                env_group,
            )

            clean_up_folders = ProcessS3Share.clean_up_share()

            if source_environment.AwsAccountId != target_environment.AwsAccountId:
                processor = ProcessLFCrossAccountShare(
                    session,
                    dataset,
                    share,
                    shared_tables,
                    revoked_tables,
                    source_environment,
                    target_environment,
                    env_group,
                )
            else:
                processor = ProcessLFSameAccountShare(
                    session,
                    dataset,
                    share,
                    shared_tables,
                    revoked_tables,
                    source_environment,
                    target_environment,
                    env_group)

                new_share_state = Share_SM.run_transition(models.Enums.ShareObjectActions.FinishReject.value)
                Share_SM.update_state(session, share, new_share_state)

            revoked_tables_succeed = processor.process_revoked_shares(revoked_item_SM)
            clean_up_tables = processor.clean_up_share()

            new_share_state = Share_SM.run_transition(models.Enums.ShareObjectActions.FinishReject.value)
            Share_SM.update_state(session, share, new_share_state)

            return revoked_tables_succeed and revoked_folders_succeed and clean_up_tables and clean_up_folders

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
                if share.status in ['Approved', 'Rejected']:
                    cls.process_share(engine, share.shareUri)

            except Exception as e:
                log.error(
                    f'Failed refreshing share {share.shareUri} with {share.status}. '
                    f'due to: {e}'
                )
        return True
