from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.base.db import exceptions
from dataall.modules.shares_base.db.share_object_models import ShareObject
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.db.share_state_machines_repositories import ShareStatusRepository
from dataall.modules.shares_base.services.share_permissions import SHARE_OBJECT_APPROVER
from dataall.modules.redshift_datasets.services.redshift_dataset_permissions import DELETE_REDSHIFT_DATASET
from dataall.modules.datasets_base.services.datasets_enums import DatasetRole, DatasetTypes
from dataall.modules.datasets_base.services.dataset_service_interface import DatasetServiceInterface


import logging

log = logging.getLogger(__name__)


class RedshiftShareDatasetService(DatasetServiceInterface):
    @property
    def dataset_type(self):
        return DatasetTypes.Redshift

    @staticmethod
    def resolve_additional_dataset_user_role(session, uri, username, groups):
        """Implemented as part of the DatasetServiceInterface"""
        share = ShareObjectRepository.find_share_by_dataset_attributes(session, uri, username, groups)
        if share is not None:
            return DatasetRole.Shared.value
        return None

    @staticmethod
    def check_before_delete(session, uri, **kwargs):
        """Implemented as part of the DatasetServiceInterface"""
        action = kwargs.get('action')
        if action in [DELETE_REDSHIFT_DATASET]:
            share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
            shares = ShareObjectRepository.list_dataset_shares_with_existing_shared_items(
                session=session, dataset_uri=uri, share_item_shared_states=share_item_shared_states
            )
            log.info(f'Found {len(shares)} shares for dataset {uri}')
            for share in shares:
                log.info(f'Share {share.shareUri} items, {share.status}')
            if shares:
                raise exceptions.ResourceShared(
                    action=DELETE_REDSHIFT_DATASET,
                    message='Revoke all dataset shares before deletion.',
                )
        return True

    @staticmethod
    def execute_on_delete(session, uri, **kwargs):
        """Implemented as part of the DatasetServiceInterface"""
        action = kwargs.get('action')
        if action in [DELETE_REDSHIFT_DATASET]:
            share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
            ShareObjectRepository.delete_dataset_shares_with_no_shared_items(session, uri, share_item_shared_states)
        return True

    @staticmethod
    def append_to_list_user_datasets(session, username, groups):
        """Implemented as part of the DatasetServiceInterface"""
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        return ShareObjectRepository.list_user_shared_datasets(
            session, username, groups, share_item_shared_states, DatasetTypes.Redshift
        )

    @staticmethod
    def extend_attach_steward_permissions(session, dataset, new_stewards, **kwargs):
        """Implemented as part of the DatasetServiceInterface"""
        dataset_shares = ShareObjectRepository.find_dataset_shares(session, dataset.datasetUri)
        if dataset_shares:
            for share in dataset_shares:
                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    group=new_stewards,
                    permissions=SHARE_OBJECT_APPROVER,
                    resource_uri=share.shareUri,
                    resource_type=ShareObject.__name__,
                )
                if dataset.stewards != dataset.SamlAdminGroupName:
                    ResourcePolicyService.delete_resource_policy(
                        session=session,
                        group=dataset.stewards,
                        resource_uri=share.shareUri,
                    )

    @staticmethod
    def extend_delete_steward_permissions(session, dataset, **kwargs):
        """Implemented as part of the DatasetServiceInterface"""
        dataset_shares = ShareObjectRepository.find_dataset_shares(session, dataset.datasetUri)
        if dataset_shares:
            for share in dataset_shares:
                if dataset.stewards != dataset.SamlAdminGroupName:
                    ResourcePolicyService.delete_resource_policy(
                        session=session,
                        group=dataset.stewards,
                        resource_uri=share.shareUri,
                    )
