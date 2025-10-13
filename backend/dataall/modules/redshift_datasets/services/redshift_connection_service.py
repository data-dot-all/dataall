import logging
from dataall.base.context import get_context
from dataall.base.db import exceptions
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.permissions.services.group_policy_service import GroupPolicyService
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.stacks.services.stack_service import StackService
from dataall.modules.redshift_datasets.db.redshift_connection_repositories import RedshiftConnectionRepository

from dataall.modules.redshift_datasets.services.redshift_connection_permissions import (
    MANAGE_REDSHIFT_CONNECTIONS,
    REDSHIFT_CONNECTION_ALL,
    REDSHIFT_GRANTABLE_PERMISSIONS,
    DELETE_REDSHIFT_CONNECTION,
    GET_REDSHIFT_CONNECTION,
    EDIT_REDSHIFT_CONNECTION_PERMISSIONS,
    CREATE_REDSHIFT_CONNECTION,
    LIST_ENVIRONMENT_REDSHIFT_CONNECTIONS,
)
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftConnection
from dataall.modules.redshift_datasets.aws.redshift_data import redshift_data_client
from dataall.modules.redshift_datasets.aws.redshift_serverless import redshift_serverless_client
from dataall.modules.redshift_datasets.aws.redshift import redshift_client
from dataall.modules.redshift_datasets.aws.kms_redshift import kms_redshift_client
from dataall.modules.redshift_datasets.services.redshift_enums import (
    RedshiftType,
    RedshiftEncryptionType,
    RedshiftConnectionTypes,
)

log = logging.getLogger(__name__)


class RedshiftConnectionService:
    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_CONNECTIONS)
    @ResourcePolicyService.has_resource_permission(CREATE_REDSHIFT_CONNECTION)
    @GroupPolicyService.has_group_permission(CREATE_REDSHIFT_CONNECTION)
    def create_redshift_connection(uri, admin_group, data: dict) -> RedshiftConnection:
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)
            connection = RedshiftConnection(
                label=data.get('connectionName'),
                owner=context.username,
                environmentUri=environment.environmentUri,
                SamlGroupName=admin_group,
                redshiftType=data.get('redshiftType'),
                clusterId=data.get('clusterId', ''),
                nameSpaceId=data.get('nameSpaceId', ''),
                workgroup=data.get('workgroup', ''),
                database=data.get('database'),
                redshiftUser=data.get('redshiftUser', ''),
                secretArn=data.get('secretArn', ''),
                connectionType=data.get('connectionType', RedshiftConnectionTypes.DATA_USER.value),
            )
            RedshiftConnectionService._check_redshift_connection(
                account_id=environment.AwsAccountId, region=environment.region, connection=connection
            )
            if connection.redshiftType == RedshiftType.Cluster.value:
                connection.nameSpaceId = redshift_client(
                    account_id=environment.AwsAccountId,
                    region=environment.region,
                ).get_cluster_namespaceId(connection.clusterId)
            connection.encryptionType = RedshiftConnectionService._get_redshift_encryption(
                account_id=environment.AwsAccountId, region=environment.region, connection=connection
            ).value
            RedshiftConnectionRepository.save_redshift_connection(session, connection)

            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=connection.SamlGroupName,
                permissions=REDSHIFT_CONNECTION_ALL,
                resource_uri=connection.connectionUri,
                resource_type=RedshiftConnection.__name__,
            )
            if connection.connectionType == RedshiftConnectionTypes.ADMIN.value:
                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    group=connection.SamlGroupName,
                    permissions=REDSHIFT_GRANTABLE_PERMISSIONS,
                    resource_uri=connection.connectionUri,
                    resource_type=RedshiftConnection.__name__,
                )
            StackService.deploy_stack(targetUri=environment.environmentUri)
            return connection

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_REDSHIFT_CONNECTION)
    def get_redshift_connection_by_uri(uri) -> RedshiftConnection:
        with get_context().db_engine.scoped_session() as session:
            connection = RedshiftConnectionRepository.get_redshift_connection(session, uri)
            if not connection:
                raise exceptions.ObjectNotFound('RedshiftConnection', uri)
            return connection

    @staticmethod
    def _get_redshift_connection(session, uri) -> RedshiftConnection:
        return RedshiftConnectionRepository.get_redshift_connection(session, uri)

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_CONNECTIONS)
    @ResourcePolicyService.has_resource_permission(DELETE_REDSHIFT_CONNECTION)
    def delete_redshift_connection(uri) -> bool:
        context = get_context()
        with context.db_engine.scoped_session() as session:
            connection = RedshiftConnectionService._get_redshift_connection(session=session, uri=uri)
            ResourcePolicyService.delete_resource_policy(
                session=session,
                resource_uri=connection.connectionUri,
                group=connection.SamlGroupName,
            )
            session.delete(connection)
            session.commit()
        StackService.deploy_stack(targetUri=connection.environmentUri)
        return True

    @staticmethod
    @ResourcePolicyService.has_resource_permission(LIST_ENVIRONMENT_REDSHIFT_CONNECTIONS)
    def list_environment_redshift_connections(uri, filter):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            connections = RedshiftConnectionRepository.paginated_user_redshift_connections(
                session, context.username, context.groups, filter
            )
            return connections

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_REDSHIFT_CONNECTION)
    def list_connection_schemas(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            connection = RedshiftConnectionService.get_redshift_connection_by_uri(uri=uri)
            environment = EnvironmentService.get_environment_by_uri(session, connection.environmentUri)
            return redshift_data_client(
                account_id=environment.AwsAccountId, region=environment.region, connection=connection
            ).list_redshift_schemas()

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_REDSHIFT_CONNECTION)
    def list_schema_tables(uri, schema):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            connection = RedshiftConnectionService.get_redshift_connection_by_uri(uri=uri)
            environment = EnvironmentService.get_environment_by_uri(session, connection.environmentUri)
            response = redshift_data_client(
                account_id=environment.AwsAccountId, region=environment.region, connection=connection
            ).list_redshift_tables(schema)
            return response

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_CONNECTIONS)
    @ResourcePolicyService.has_resource_permission(EDIT_REDSHIFT_CONNECTION_PERMISSIONS)
    def add_group_permissions(uri, group, permissions) -> bool:
        context = get_context()
        connection = RedshiftConnectionService.get_redshift_connection_by_uri(uri=uri)
        RedshiftConnectionService._check_redshift_connection_has_grantable_permissions(connection)
        if any(permission not in REDSHIFT_GRANTABLE_PERMISSIONS for permission in permissions):
            raise exceptions.InvalidInput(
                param_name='Permissions',
                param_value=permissions,
                constraint=f'one of the possible grantable permissions {REDSHIFT_GRANTABLE_PERMISSIONS}',
            )
        env_groups = EnvironmentService.list_all_environment_groups(uri=connection.environmentUri)
        with context.db_engine.scoped_session() as session:
            if group not in env_groups:
                raise exceptions.InvalidInput(
                    param_name='Team', param_value=group, constraint='a team invited to the Environment.'
                )
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=group,
                permissions=permissions,
                resource_uri=uri,
                resource_type=RedshiftConnection.__name__,
            )
        return True

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_CONNECTIONS)
    @ResourcePolicyService.has_resource_permission(EDIT_REDSHIFT_CONNECTION_PERMISSIONS)
    def delete_group_permissions(uri, group) -> bool:
        context = get_context()
        connection = RedshiftConnectionService.get_redshift_connection_by_uri(uri=uri)
        RedshiftConnectionService._check_redshift_connection_has_grantable_permissions(connection)
        if connection.SamlGroupName == group:
            raise exceptions.InvalidInput(
                param_name='Team', param_value=group, constraint='any team EXCEPT the connection owners team.'
            )
        with context.db_engine.scoped_session() as session:
            ResourcePolicyService.delete_resource_policy(
                session=session,
                group=group,
                resource_uri=uri,
                resource_type=RedshiftConnection.__name__,
            )
        return True

    @staticmethod
    @ResourcePolicyService.has_resource_permission(EDIT_REDSHIFT_CONNECTION_PERMISSIONS)
    def list_connection_group_permissions(uri, filter):
        context = get_context()
        permissions = REDSHIFT_GRANTABLE_PERMISSIONS
        with context.db_engine.scoped_session() as session:
            return RedshiftConnectionRepository.paginated_redshift_connection_group_permissions(
                session, uri, permissions, filter
            )

    @staticmethod
    @ResourcePolicyService.has_resource_permission(EDIT_REDSHIFT_CONNECTION_PERMISSIONS)
    def list_connection_group_no_permissions(uri, filter):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            connection = RedshiftConnectionService.get_redshift_connection_by_uri(uri=uri)
            RedshiftConnectionService._check_redshift_connection_has_grantable_permissions(connection)
            return RedshiftConnectionRepository.list_redshift_connection_group_no_permissions(
                session, uri, connection.environmentUri, filter
            )

    @staticmethod
    def _check_redshift_connection(account_id: str, region: str, connection: RedshiftConnection):
        if connection.redshiftType == RedshiftType.Serverless.value:
            if (
                namespace := redshift_serverless_client(account_id=account_id, region=region).get_namespace_by_id(
                    connection.nameSpaceId
                )
            ) is None:
                raise Exception(
                    f'Redshift namespaceId {connection.nameSpaceId} does not exist. Remember to introduce the Id and not the name of the namespace.'
                )
            if connection.workgroup and connection.workgroup not in [
                workgroup['workgroupName']
                for workgroup in redshift_serverless_client(
                    account_id=account_id, region=region
                ).list_workgroups_in_namespace(namespace['namespaceName'])
            ]:
                raise Exception(
                    f'Redshift workgroup {connection.workgroup} does not exist or is not associated to namespace {connection.nameSpaceId}'
                )

        if connection.redshiftType == RedshiftType.Cluster.value:
            cluster = redshift_client(account_id=account_id, region=region).describe_cluster(connection.clusterId)
            if not cluster:
                raise Exception(
                    f'Redshift cluster {connection.clusterId} does not exist or cannot be accessed with these parameters'
                )
            if not cluster.get('Encrypted', False):
                raise Exception(
                    f'Redshift cluster {connection.clusterId} is not encrypted. Data.all clusters MUST be encrypted'
                )
        try:
            redshift_data_client(
                account_id=account_id, region=region, connection=connection
            ).get_redshift_connection_database()
        except Exception as e:
            raise Exception(
                f'Redshift database {connection.database} does not exist or cannot be accessed with these parameters: {e}'
            )
        return

    @staticmethod
    def _get_redshift_encryption(
        account_id: str, region: str, connection: RedshiftConnection
    ) -> RedshiftEncryptionType:
        if connection.redshiftType == RedshiftType.Serverless.value:
            namespace = redshift_serverless_client(account_id=account_id, region=region).get_namespace_by_id(
                connection.nameSpaceId
            )
            return (
                RedshiftEncryptionType.AWS_OWNED_KMS_KEY
                if namespace.get('kmsKeyId', None) == RedshiftEncryptionType.AWS_OWNED_KMS_KEY.value
                else RedshiftEncryptionType.CUSTOMER_MANAGED_KMS_KEY
            )
        if connection.redshiftType == RedshiftType.Cluster.value:
            cluster = redshift_client(account_id=account_id, region=region).describe_cluster(connection.clusterId)
            if key_id := cluster.get('KmsKeyId', None):
                key = kms_redshift_client(account_id=account_id, region=region).describe_kms_key(key_id=key_id)
                if key.get('KeyManager', None) == 'AWS':
                    return RedshiftEncryptionType.AWS_OWNED_KMS_KEY
                elif key.get('KeyManager', None) == 'CUSTOMER':
                    return RedshiftEncryptionType.CUSTOMER_MANAGED_KMS_KEY
                else:
                    raise Exception
            if cluster.get('HsmStatus', None):
                return RedshiftEncryptionType.HSM
        raise Exception

    @staticmethod
    def _check_redshift_connection_has_grantable_permissions(connection: RedshiftConnection):
        if connection.connectionType != RedshiftConnectionTypes.ADMIN.value:
            raise exceptions.InvalidInput(
                param_name='ConnectionType',
                param_value=connection.connectionType,
                constraint=f'of type {RedshiftConnectionTypes.ADMIN.value}. Only ADMIN connections support granting additional permissions.',
            )
        return True
