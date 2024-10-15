from dataall.base.context import get_context
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.modules.shares_base.services.share_object_service import SharesValidatorInterface
from dataall.modules.shares_base.services.share_exceptions import PrincipalRoleNotFound, InvalidConfiguration
from dataall.modules.shares_base.services.share_permissions import (
    CREATE_SHARE_OBJECT,
    SUBMIT_SHARE_OBJECT,
    APPROVE_SHARE_OBJECT,
)
from dataall.modules.redshift_datasets_shares.aws.redshift_data import redshift_share_data_client
from dataall.modules.redshift_datasets.db.redshift_connection_repositories import RedshiftConnectionRepository
from dataall.modules.redshift_datasets.db.redshift_dataset_repositories import RedshiftDatasetRepository
from dataall.modules.redshift_datasets.services.redshift_connection_permissions import (
    CREATE_SHARE_REQUEST_WITH_CONNECTION,
)

import logging

log = logging.getLogger(__name__)


class RedshiftTableValidator(SharesValidatorInterface):
    @staticmethod
    def validate_share_object_create(
        session,
        dataset,
        group_uri,
        environment,
        principal_type,
        principal_id,
        principal_role_name,
        attachMissingPolicies,
        permissions,
    ) -> bool:
        RedshiftTableValidator._validate_target_connection_permissions(session=session, uri=principal_id)
        rs_dataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(
            session=session, dataset_uri=dataset.datasetUri
        )
        RedshiftTableValidator._validate_source_connection(
            session=session, dataset_connection_uri=rs_dataset.connectionUri
        )
        RedshiftTableValidator._validate_clusters(
            session=session, source_connection_uri=rs_dataset.connectionUri, target_connection_uri=principal_id
        )
        RedshiftTableValidator._validate_redshift_role(
            session=session,
            environment=environment,
            principal_id=principal_id,
            principal_role_name=principal_role_name,
            action=CREATE_SHARE_OBJECT,
        )
        return True

    @staticmethod
    def validate_share_object_submit(session, dataset, share) -> bool:
        environment = EnvironmentService.get_environment_by_uri(session, share.environmentUri)
        RedshiftTableValidator._validate_redshift_role(
            session=session,
            environment=environment,
            principal_id=share.principalId,
            principal_role_name=share.principalRoleName,
            action=SUBMIT_SHARE_OBJECT,
        )
        return True

    @staticmethod
    def validate_share_object_approve(session, dataset, share) -> bool:
        environment = EnvironmentService.get_environment_by_uri(session, share.environmentUri)
        RedshiftTableValidator._validate_redshift_role(
            session=session,
            environment=environment,
            principal_id=share.principalId,
            principal_role_name=share.principalRoleName,
            action=APPROVE_SHARE_OBJECT,
        )
        return True

    @staticmethod
    def _validate_redshift_role(session, environment, action, principal_id: str, principal_role_name: str):
        log.info(
            f'Verifying share request provided Redshift role {principal_role_name} exists in connection {principal_id}...'
        )
        connection = RedshiftConnectionRepository.get_redshift_connection(session, uri=principal_id)
        client = redshift_share_data_client(
            account_id=environment.AwsAccountId, region=environment.region, connection=connection
        )
        if not client.check_redshift_role_in_namespace(role=principal_role_name):
            raise PrincipalRoleNotFound(
                action=action,
                message=f'The principal Redshift role {principal_role_name} does not exist or is not accessible for the Redshift connection {connection.name}.',
            )

    @staticmethod
    def _validate_clusters(session, source_connection_uri, target_connection_uri):
        log.info('Verifying share request clusters are different...')
        source_connection = RedshiftConnectionRepository.get_redshift_connection(session, uri=source_connection_uri)
        target_connection = RedshiftConnectionRepository.get_redshift_connection(session, uri=target_connection_uri)
        if source_connection.nameSpaceId == target_connection.nameSpaceId:
            raise InvalidConfiguration(
                action=CREATE_SHARE_OBJECT,
                message='Redshift data.all datashares are only possible between different namespaces',
            )

    @staticmethod
    def _validate_source_connection(session, dataset_connection_uri):
        log.info('Verifying source namespace has an admin connection...')
        dataset_connection = RedshiftConnectionRepository.get_redshift_connection(session, uri=dataset_connection_uri)
        if not RedshiftConnectionRepository.get_namespace_admin_connection(
            session, environment_uri=dataset_connection.environmentUri, namespace_id=dataset_connection.nameSpaceId
        ):
            raise InvalidConfiguration(
                action=CREATE_SHARE_OBJECT,
                message='Redshift data.all datashares require an ADMIN connection in the SOURCE namespace',
            )

    @staticmethod
    def _validate_target_connection_permissions(session, uri):
        context = get_context()
        return ResourcePolicyService.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=uri,
            permission_name=CREATE_SHARE_REQUEST_WITH_CONNECTION,
        )
