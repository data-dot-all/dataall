import logging
from dataclasses import dataclass

from typing import Any
from dataall.core.resource_lock.db.resource_lock_repositories import ResourceLockRepository
from dataall.base.db import Engine
from dataall.core.environment.db.environment_models import ConsumptionRole, Environment, EnvironmentGroup
from dataall.modules.shares_base.db.share_object_state_machines import (
    ShareObjectSM,
    ShareItemSM,
)
from dataall.modules.shares_base.services.shares_enums import (
    ShareItemHealthStatus,
    ShareObjectActions,
    ShareItemActions,
    ShareItemStatus,
    PrincipalType,
)
from dataall.modules.shares_base.db.share_object_models import ShareObject
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.db.share_state_machines_repositories import ShareStatusRepository
from dataall.modules.shares_base.services.share_processor_manager import ShareProcessorManager
from dataall.modules.shares_base.services.share_object_service import (
    ShareObjectService,
)
from dataall.modules.shares_base.services.share_exceptions import PrincipalRoleNotFound
from dataall.base.db.exceptions import ResourceLockTimeout

log = logging.getLogger(__name__)


@dataclass
class ShareData:
    share: ShareObject
    dataset: Any
    source_environment: Environment
    target_environment: Environment
    source_env_group: EnvironmentGroup
    env_group: EnvironmentGroup


class SharingService:
    @classmethod
    def approve_share(cls, engine: Engine, share_uri: str) -> bool:
        """
        1) Updates share object State Machine with the Action: Start
        2) Retrieves share data and items in Share_Approved state
        3) Verifies principal IAM Role
        4) Acquires dataset lock and locks dataset while sharing
        5) Calls corresponding SharesInterface.process_approved_shares for available items
        6) [Finally] Updates share object State Machine with the Action: Finish and releases dataset lock

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns
        -------
        True if sharing succeeds,
        False if sharing fails
        """
        with engine.scoped_session() as session:
            share_data, share_items = cls._get_share_data_and_items(
                session, share_uri, ShareItemStatus.Share_Approved.value
            )
            share_object_sm = ShareObjectSM(share_data.share.status)
            share_item_sm = ShareItemSM(ShareItemStatus.Share_Approved.value)

            log.info(f'Starting share {share_data.share.shareUri}')
            new_share_state = share_object_sm.run_transition(ShareObjectActions.Start.value)
            share_object_sm.update_state(session, share_data.share, new_share_state)

            resources = [(share_data.dataset.datasetUri, share_data.dataset.__tablename__)]
            resources.append(
                (share_data.share.principalId, ConsumptionRole.__tablename__)
                if share_data.share.principalType == PrincipalType.ConsumptionRole.value
                else (
                    f'{share_data.share.principalId}-{share_data.share.environmentUri}',
                    EnvironmentGroup.__tablename__,
                )
            )

            share_successful = True
            try:
                if share_data.share.principalType in [PrincipalType.ConsumptionRole.value, PrincipalType.Group.value]:
                    # TODO make it generic to non IAM role principals
                    if not ShareObjectService.verify_principal_role(session, share_data.share):
                        raise PrincipalRoleNotFound(
                            'process approved shares',
                            f'Principal role {share_data.share.principalRoleName} is not found.',
                        )

                with ResourceLockRepository.acquire_lock_with_retry(
                    resources=resources,
                    session=session,
                    acquired_by_uri=share_data.share.shareUri,
                    acquired_by_type=share_data.share.__tablename__,
                ):
                    for type, processor in ShareProcessorManager.SHARING_PROCESSORS.items():
                        try:
                            log.info(f'Granting permissions of {type.value}')
                            shareable_items = ShareObjectRepository.get_share_data_items_by_type(
                                session,
                                share_data.share,
                                processor.shareable_type,
                                processor.shareable_uri,
                                status=ShareItemStatus.Share_Approved.value,
                            )
                            if shareable_items:
                                success = processor.Processor(
                                    session, share_data, shareable_items
                                ).process_approved_shares()
                                log.info(f'Sharing {type.value} succeeded = {success}')
                                if not success:
                                    share_successful = False
                            else:
                                log.info(f'There are no items to share of type{type.value}')
                        except Exception as e:
                            log.exception(f'Error occurred during sharing of {type.value}')
                            ShareStatusRepository.update_share_item_status_batch(
                                session,
                                share_uri,
                                old_status=ShareItemStatus.Share_Approved.value,
                                new_status=ShareItemStatus.Share_Failed.value,
                                share_item_type=processor.type,
                            )
                            ShareStatusRepository.update_share_item_status_batch(
                                session,
                                share_uri,
                                old_status=ShareItemStatus.Share_In_Progress.value,
                                new_status=ShareItemStatus.Share_Failed.value,
                                share_item_type=processor.type,
                            )
                            share_successful = False
                return share_successful

            except Exception as e:
                log.exception('Error occurred during share approval')
                new_share_item_state = share_item_sm.run_transition(ShareItemActions.Failure.value)
                share_item_sm.update_state(session, share_data.share.shareUri, new_share_item_state)
                return False

            finally:
                new_share_state = share_object_sm.run_transition(ShareObjectActions.Finish.value)
                share_object_sm.update_state(session, share_data.share, new_share_state)

    @classmethod
    def revoke_share(cls, engine: Engine, share_uri: str) -> bool:
        """
        1) Updates share object State Machine with the Action: Start
        2) Retrieves share data and items in Revoke_Approved state
        3) Acquires dataset lock and locks dataset while revoking
        4) Calls corresponding SharesInterface.process_revoke_shares for available items
        5) [Finally] Updates share object State Machine with the Action: Finish or FinishPending and releases dataset lock

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns
        -------
        True if revoking succeeds
        False if revoking failed
        """
        with engine.scoped_session() as session:
            share_data, share_items = cls._get_share_data_and_items(
                session, share_uri, ShareItemStatus.Revoke_Approved.value
            )

            share_sm = ShareObjectSM(share_data.share.status)
            share_item_sm = ShareItemSM(ShareItemStatus.Revoke_Approved.value)

            log.info(f'Starting revoke {share_data.share.shareUri}')
            new_share_state = share_sm.run_transition(ShareObjectActions.Start.value)
            share_sm.update_state(session, share_data.share, new_share_state)

            resources = [(share_data.dataset.datasetUri, share_data.dataset.__tablename__)]
            resources.append(
                (share_data.share.principalId, ConsumptionRole.__tablename__)
                if share_data.share.principalType == PrincipalType.ConsumptionRole.value
                else (
                    f'{share_data.share.principalId}-{share_data.share.environmentUri}',
                    EnvironmentGroup.__tablename__,
                )
            )

            revoke_successful = True
            try:
                if share_data.share.principalType in [PrincipalType.ConsumptionRole.value, PrincipalType.Group.value]:
                    # TODO make it generic to non IAM role principals
                    if not ShareObjectService.verify_principal_role(session, share_data.share):
                        raise PrincipalRoleNotFound(
                            'process revoked shares',
                            f'Principal role {share_data.share.principalRoleName} is not found.',
                        )

                with ResourceLockRepository.acquire_lock_with_retry(
                    resources=resources,
                    session=session,
                    acquired_by_uri=share_data.share.shareUri,
                    acquired_by_type=share_data.share.__tablename__,
                ):
                    for type, processor in ShareProcessorManager.SHARING_PROCESSORS.items():
                        try:
                            shareable_items = ShareObjectRepository.get_share_data_items_by_type(
                                session,
                                share_data.share,
                                processor.shareable_type,
                                processor.shareable_uri,
                                status=ShareItemStatus.Revoke_Approved.value,
                            )
                            log.info(f'Revoking permissions with {type.value}')
                            success = processor.Processor(session, share_data, shareable_items).process_revoked_shares()
                            log.info(f'Revoking {type.value} succeeded = {success}')
                            if not success:
                                revoke_successful = False
                        except Exception as e:
                            log.error(f'Error occurred during share revoking of {type.value}: {e}')
                            ShareStatusRepository.update_share_item_status_batch(
                                session,
                                share_uri,
                                old_status=ShareItemStatus.Revoke_Approved.value,
                                new_status=ShareItemStatus.Revoke_Failed.value,
                                share_item_type=processor.type,
                            )
                            ShareStatusRepository.update_share_item_status_batch(
                                session,
                                share_uri,
                                old_status=ShareItemStatus.Revoke_In_Progress.value,
                                new_status=ShareItemStatus.Revoke_Failed.value,
                                share_item_type=processor.type,
                            )
                            revoke_successful = False

                return revoke_successful
            except Exception as e:
                log.error(f'Error occurred during share revoking: {e}')
                new_share_item_state = share_item_sm.run_transition(ShareItemActions.Failure.value)
                share_item_sm.update_state(session, share_data.share.shareUri, new_share_item_state)
                return False

            finally:
                existing_pending_items = ShareStatusRepository.check_pending_share_items(session, share_uri)
                if existing_pending_items:
                    new_share_state = share_sm.run_transition(ShareObjectActions.FinishPending.value)
                else:
                    new_share_state = share_sm.run_transition(ShareObjectActions.Finish.value)
                share_sm.update_state(session, share_data.share, new_share_state)

    @classmethod
    def verify_share(
        cls,
        engine: Engine,
        share_uri: str,
        status: str = None,
        healthStatus: str = ShareItemHealthStatus.PendingVerify.value,
    ) -> bool:
        """
        1) Retrieves share data and items in specified status and health state (by default - PendingVerify)
        2) Calls corresponding SharesInterface.verify_shares

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns True when completed
        -------
        """
        with engine.scoped_session() as session:
            share_data, share_items = cls._get_share_data_and_items(session, share_uri, status, healthStatus)
            if share_data.share.principalType in [PrincipalType.ConsumptionRole.value, PrincipalType.Group.value]:
                # TODO make it generic to non IAM role principals
                log.info(f'Verifying principal IAM Role {share_data.share.principalRoleName}')
                if not ShareObjectService.verify_principal_role(session, share_data.share):
                    log.error(
                        f'Failed to get Principal IAM Role {share_data.share.principalRoleName}, updating health status...'
                    )
                    ShareStatusRepository.update_share_item_health_status_batch(
                        session,
                        share_uri,
                        old_status=healthStatus,
                        new_status=ShareItemHealthStatus.Unhealthy.value,
                        message=f'Share principal Role {share_data.share.principalRoleName} not found. Check the team or consumption IAM role used.',
                    )
                    return True

            for type, processor in ShareProcessorManager.SHARING_PROCESSORS.items():
                try:
                    shareable_items = ShareObjectRepository.get_share_data_items_by_type(
                        session,
                        share_data.share,
                        processor.shareable_type,
                        processor.shareable_uri,
                        status=status,
                        healthStatus=healthStatus,
                    )
                    log.info(f'Verifying permissions with {type.value}')
                    processor.Processor(session, share_data, shareable_items).verify_shares()
                except Exception as e:
                    log.error(f'Error occurred during share verifying of {type.value}: {e}')

        return True

    @classmethod
    def reapply_share(cls, engine: Engine, share_uri: str) -> bool:
        """
        1) Retrieves share data and items in PendingReApply health state
        2) Calls sharing folders processor to re-apply share + update share item(s) health status
        3) Calls sharing buckets processor to re-apply share + update share item(s) health status
        4) Calls sharing tables processor for same or cross account sharing to re-apply share + update share item(s) health status

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns
        -------
        True if re-apply of share item(s) succeeds,
        False if any re-apply of share item(s) failed
        """
        reapply_successful = True
        with engine.scoped_session() as session:
            share_data, share_items = cls._get_share_data_and_items(
                session, share_uri, None, ShareItemHealthStatus.PendingReApply.value
            )
            resources = [(share_data.dataset.datasetUri, share_data.dataset.__tablename__)]
            resources.append(
                (share_data.share.principalId, ConsumptionRole.__tablename__)
                if share_data.share.principalType == PrincipalType.ConsumptionRole.value
                else (
                    f'{share_data.share.principalId}-{share_data.share.environmentUri}',
                    EnvironmentGroup.__tablename__,
                )
            )

            try:
                if share_data.share.principalType in [PrincipalType.ConsumptionRole.value, PrincipalType.Group.value]:
                    # TODO make it generic to non IAM role principals
                    log.info(f'Verifying principal IAM Role {share_data.share.principalRoleName}')
                    reapply_successful = ShareObjectService.verify_principal_role(session, share_data.share)
                    if not reapply_successful:
                        log.error(f'Failed to get Principal IAM Role {share_data.share.principalRoleName}, exiting...')
                        return False
                with ResourceLockRepository.acquire_lock_with_retry(
                    resources=resources,
                    session=session,
                    acquired_by_uri=share_data.share.shareUri,
                    acquired_by_type=share_data.share.__tablename__,
                ):
                    for type, processor in ShareProcessorManager.SHARING_PROCESSORS.items():
                        try:
                            log.info(f'Reapplying permissions to {type.value}')
                            shareable_items = ShareObjectRepository.get_share_data_items_by_type(
                                session,
                                share_data.share,
                                processor.shareable_type,
                                processor.shareable_uri,
                                None,
                                ShareItemHealthStatus.PendingReApply.value,
                            )
                            success = processor.Processor(
                                session, share_data, shareable_items
                            ).process_approved_shares()
                            log.info(f'Reapplying {type.value} succeeded = {success}')
                            if not success:
                                reapply_successful = False
                        except Exception as e:
                            log.error(f'Error occurred during share reapplying of {type.value}: {e}')

                return reapply_successful

            except ResourceLockTimeout as e:
                ShareStatusRepository.update_share_item_health_status_batch(
                    session,
                    share_uri,
                    old_status=ShareItemHealthStatus.PendingReApply.value,
                    new_status=ShareItemHealthStatus.Unhealthy.value,
                    message=str(e),
                )

            except Exception as e:
                log.exception('Error occurred during share approval')
                return False

    @staticmethod
    def _get_share_data_and_items(session, share_uri, status, healthStatus=None):
        data = ShareObjectRepository.get_share_data(session, share_uri)
        share_data = ShareData(
            share=data[0],
            dataset=data[1],
            source_environment=data[2],
            target_environment=data[3],
            source_env_group=data[4],
            env_group=data[5],
        )
        share_items = ShareObjectRepository.get_all_share_items_in_share(
            session=session, share_uri=share_uri, status=[status], healthStatus=[healthStatus]
        )
        return share_data, share_items
