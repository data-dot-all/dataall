from dataall.modules.shares_base.services.share_object_service import SharesCreationValidatorInterface
from dataall.modules.shares_base.services.share_exceptions import PrincipalRoleNotFound, InvalidConfiguration
from dataall.modules.shares_base.services.share_permissions import (
    CREATE_SHARE_OBJECT,
)
from dataall.modules.redshift_datasets_shares.aws.redshift_data import redshift_share_data_client
from dataall.modules.redshift_datasets.db.redshift_connection_repositories import RedshiftConnectionRepository
from dataall.modules.redshift_datasets.db.redshift_dataset_repositories import RedshiftDatasetRepository

import logging

log = logging.getLogger(__name__)


class RedshiftTableValidator(SharesCreationValidatorInterface):
    @staticmethod
    def validate_share_object_create(session, dataset_uri, *args, **kwargs) -> bool:
        principal_id = kwargs.get('principal_id')
        dataset_connection_uri = kwargs.get('dataset_connection_uri')
        RedshiftTableValidator._validate_clusters(session=session, dataset_uri=dataset_uri, principal_id=principal_id)
        RedshiftTableValidator._validate_redshift_role(
            session=session,
            environment=kwargs.get('environment'),
            principal_id=principal_id,
            principal_role_name=kwargs.get('principal_role_name'),
        )
        RedshiftTableValidator._validate_source_connection(
            session=session, dataset_connection_uri=dataset_connection_uri
        )
        return True

    @staticmethod
    def validate_share_object_submit(session, dataset, *args, **kwargs) -> bool:
        principal_id = kwargs.get('principal_id')
        RedshiftTableValidator._validate_redshift_role(
            session=session,
            environment=kwargs.get('environment'),
            principal_id=principal_id,
            principal_role_name=kwargs.get('principal_role_name'),
        )

    @staticmethod
    def validate_share_object_approve(session, dataset, *args, **kwargs) -> bool:
        principal_id = kwargs.get('principal_id')
        RedshiftTableValidator._validate_redshift_role(
            session=session,
            environment=kwargs.get('environment'),
            principal_id=principal_id,
            principal_role_name=kwargs.get('principal_role_name'),
        )

    @staticmethod
    def _validate_redshift_role(session, environment, principal_id: str, principal_role_name: str):
        log.info('Verifying share request provided Redshift role exists...')
        connection = RedshiftConnectionRepository.get_redshift_connection(session, uri=principal_id)
        client = redshift_share_data_client(
            account_id=environment.AwsAccountId, region=environment.region, connection=connection
        )
        if not client.check_redshift_role_in_namespace(role=principal_role_name):
            raise PrincipalRoleNotFound(
                action=CREATE_SHARE_OBJECT,
                message=f'The principal Redshift role {principal_role_name} does not exist or is not accessible for the Redshift connection {connection.name}.',
            )

    @staticmethod
    def _validate_clusters(session, dataset_uri, principal_id):
        log.info('Verifying share request clusters are different...')
        rs_dataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session=session, dataset_uri=dataset_uri)
        source_connection = RedshiftConnectionRepository.get_redshift_connection(session, uri=rs_dataset.connectionUri)
        target_connection = RedshiftConnectionRepository.get_redshift_connection(session, uri=principal_id)
        if source_connection.nameSpaceId == target_connection.nameSpaceId:
            raise InvalidConfiguration(
                action=CREATE_SHARE_OBJECT,
                message='Redshift data.all datashares are only possible between different namespaces',
            )

    @staticmethod
    def _validate_source_connection(session, dataset_connection_uri):
        log.info('Verifying source namespace has an admin connection...')
        dataset_connection = RedshiftConnectionRepository.list_environment_redshift_connections(
            session, dataset_connection_uri
        )
        if not RedshiftConnectionRepository.get_namespace_admin_connection(
            session, namespace_id=dataset_connection.nameSpaceId
        ):
            raise InvalidConfiguration(
                action=CREATE_SHARE_OBJECT,
                message='Redshift data.all datashares require an ADMIN connection in both clusters',
            )
