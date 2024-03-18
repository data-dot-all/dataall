from dataall.base.context import get_context
from dataall.base.db import exceptions
from dataall.base.aws.secrets_manager import SecretsManager
from dataall.base.aws.iam import IAM
from dataall.core.permissions.permission_checker import has_resource_permission, has_tenant_permission
from dataall.core.environment.env_permission_checker import has_group_permission
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.modules.warehouses.db.warehouse_models import WarehouseConsumer, WarehouseConnection
from dataall.modules.warehouses.db.warehouse_repository import WarehouseRepository
from dataall.modules.warehouses.services.warehouse_permissions import (
    CREATE_WAREHOUSE_CONNECTION,
    CREATE_WAREHOUSE_CONSUMER,
    DELETE_WAREHOUSE_CONNECTION,
    DELETE_WAREHOUSE_CONSUMER,
    MANAGE_WAREHOUSES,
    UPDATE_WAREHOUSE_CONNECTION,
    UPDATE_WAREHOUSE_CONSUMER,
    WAREHOUSE_CONNECTION_ALL,
    WAREHOUSE_CONSUMER_ALL,
)
from dataall.modules.warehouses.aws.redshift_serverless_warehouse_client import redshift_serverless_client
from dataall.modules.warehouses.aws.redshift_warehouse_client import redshift_client
from dataall.modules.warehouses.services.warehouse_enums import AuthenticationType, ConsumerType, WarehouseType


class WarehouseService:
    """
    Encapsulate the logic of interactions with Warehouses objects: connections, consumers.
    """

    @has_tenant_permission(MANAGE_WAREHOUSES)
    @has_resource_permission(CREATE_WAREHOUSE_CONNECTION)
    @has_group_permission(CREATE_WAREHOUSE_CONNECTION)
    @staticmethod
    def create_warehouse_connection(*, uri: str, admin_group: str, input: dict):
        with _session() as session:
            env = EnvironmentService.get_environment_by_uri(session, uri)
            enabled = EnvironmentService.get_boolean_env_param(session, env, 'warehousesEnabled')

            if not enabled:
                raise exceptions.UnauthorizedOperation(
                    action=CREATE_WAREHOUSE_CONNECTION,
                    message=f'Warehouses feature is disabled for the environment {env.label}',
                )

            _validate_redshift_infra(env.AwsAccountId, env.region, input.get('warehouseType'), input.get('warehouseId'))
            _validate_connection(
                env.AwsAccountId, env.region, input.get('connectionType'), input.get('connectionDetails')
            )

            connection = WarehouseConnection(
                environmentUri=env.environmentUri,
                AwsAccountId=env.AwsAccountId,
                region=env.region,
                SamlAdminGroupName=admin_group,
                name=input.get('name'),
                warehouseId=input.get('warehouseId'),
                warehouseType=input.get('warehouseType'),
                databaseName=input.get('databaseName'),
                authenticationType=input.get('authenticationType'),
                authenticationDetails=input.get('authenticationDetails'),
            )
            WarehouseRepository(session).save_item(connection)

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=admin_group,
                permissions=WAREHOUSE_CONNECTION_ALL,
                resource_uri=connection.connectionUri,
                resource_type=WarehouseConnection.__name__,
            )
        return

    @has_tenant_permission(MANAGE_WAREHOUSES)
    @has_resource_permission(CREATE_WAREHOUSE_CONSUMER)
    @has_group_permission(CREATE_WAREHOUSE_CONSUMER)
    @staticmethod
    def create_warehouse_consumer(*, uri: str, admin_group: str, input: dict):
        with _session() as session:
            env = EnvironmentService.get_environment_by_uri(session, uri)
            enabled = EnvironmentService.get_boolean_env_param(session, env, 'warehousesEnabled')

            if not enabled:
                raise exceptions.UnauthorizedOperation(
                    action=CREATE_WAREHOUSE_CONSUMER,
                    message=f'Warehouses feature is disabled for the environment {env.label}',
                )

            _validate_redshift_infra(env.AwsAccountId, env.region, input.get('warehouseType'), input.get('warehouseId'))
            _validate_consumer(env.AwsAccountId, env.region, input.get('consumerType'), input.get('consumerDetails'))

            consumer = WarehouseConsumer(
                environmentUri=env.environmentUri,
                AwsAccountId=env.AwsAccountId,
                region=env.region,
                SamlAdminGroupName=admin_group,
                name=input.get('name'),
                warehouseId=input.get('warehouseId'),
                warehouseType=input.get('warehouseType'),
                consumerType=input.get('consumerType'),
                consumerDetails=input.get('consumerDetails'),
            )

            WarehouseRepository(session).save_item(consumer)

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=admin_group,
                permissions=WAREHOUSE_CONSUMER_ALL,
                resource_uri=consumer.consumerUri,
                resource_type=WarehouseConsumer.__name__,
            )
        return

    @has_resource_permission(UPDATE_WAREHOUSE_CONNECTION)
    @staticmethod
    def update_warehouse_connection(uri, data=None):
        with _session() as session:
            connection = WarehouseService._get_connection(session, uri)
            if data.get('SamlAdminGroupName'):
                ResourcePolicy.delete_resource_policy(
                    session=session,
                    resource_uri=connection.connectionUri,
                    group=connection.SamlAdminGroupName,
                )
                connection['SamlAdminGroupName'] = data.get('SamlAdminGroupName')
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=data.get('SamlAdminGroupName'),
                    permissions=WAREHOUSE_CONNECTION_ALL,
                    resource_uri=connection.connectionUri,
                    resource_type=WarehouseConnection.__name__,
                )
            if data.get('name'):
                connection['name'] = data.get('name')
            if data.get('connectionDetails'):
                _validate_connection(
                    connection.AwsAccountId, connection.region, connection.connectionType, data.get('connectionDetails')
                )
                connection['connectionDetails'] = data.get('connectionDetails')
        return

    @has_resource_permission(UPDATE_WAREHOUSE_CONSUMER)
    @staticmethod
    def update_warehouse_consumer(uri, data=None):
        with _session() as session:
            consumer = WarehouseService._get_consumer(session, uri)
            if data.get('SamlAdminGroupName'):
                ResourcePolicy.delete_resource_policy(
                    session=session,
                    resource_uri=consumer.consumerUri,
                    group=consumer.SamlAdminGroupName,
                )
                consumer['SamlAdminGroupName'] = data.get('SamlAdminGroupName')
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=data.get('SamlAdminGroupName'),
                    permissions=WAREHOUSE_CONSUMER_ALL,
                    resource_uri=consumer.connectionUri,
                    resource_type=WarehouseConsumer.__name__,
                )
            if data.get('name'):
                consumer['name'] = data.get('name')
            if data.get('consumerDetails'):
                _validate_consumer(
                    consumer.AwsAccountId, consumer.region, consumer.consumerType, data.get('consumerDetails')
                )
                consumer['consumerDetails'] = data.get('consumerDetails')
        return

    @has_resource_permission(DELETE_WAREHOUSE_CONNECTION)
    @staticmethod
    def delete_warehouse_connection(uri):
        with _session() as session:
            connection = WarehouseService._get_connection(session, uri)
            WarehouseRepository(session).delete_item(connection)
            ResourcePolicy.delete_resource_policy(
                session=session,
                resource_uri=connection.connectionUri,
                group=connection.SamlAdminGroupName,
            )
        return True

    @has_resource_permission(DELETE_WAREHOUSE_CONSUMER)
    @staticmethod
    def delete_warehouse_consumer(uri):
        with _session() as session:
            consumer = WarehouseService._get_consumer(session, uri)
            WarehouseRepository(session).delete_item(consumer)

            ResourcePolicy.delete_resource_policy(
                session=session,
                resource_uri=consumer.consumerUri,
                group=consumer.SamlAdminGroupName,
            )
        return True

    @staticmethod
    def list_warehouse_connections(filter):
        with _session() as session:
            return WarehouseRepository(session).paginated_user_connections(
                username=get_context().username, groups=get_context().groups, filter=filter
            )

    @staticmethod
    def list_warehouse_consumers(filter):
        with _session() as session:
            return WarehouseRepository(session).paginated_user_consumers(
                username=get_context().username, groups=get_context().groups, filter=filter
            )

    @staticmethod
    def _get_connection(session, uri) -> WarehouseConnection:
        connection = WarehouseRepository(session).find_warehouse_connection(uri)
        if not connection:
            raise exceptions.ObjectNotFound('WarehouseConnection', uri)
        return connection

    @staticmethod
    def _get_consumer(session, uri) -> WarehouseConsumer:
        consumer = WarehouseRepository(session).find_warehouse_consumer(uri)
        if not consumer:
            raise exceptions.ObjectNotFound('WarehouseConsumer', uri)
        return consumer


def _validate_redshift_infra(AwsAccountId, region, warehouseType, warehouseId):
    if warehouseType == WarehouseType.RedshiftServerless.value:
        client = redshift_serverless_client(AwsAccountId, region)
        client.get_namespace(warehouseId)
    else:
        client = redshift_client(AwsAccountId, region)
        client.get_cluster(warehouseId)


def _validate_connection(AwsAccountId, region, connectionType, connectionDetails):
    if connectionType == AuthenticationType.SecretsManager.value:
        SecretsManager(account_id=AwsAccountId, region=region).get_secret_value(secret_id=connectionDetails)
    else:
        IAM.get_role(account_id=AwsAccountId, role_arn=connectionDetails)
        # TODO: REVIEW IF WE NEED FURTHER VALIDATION = e.g. Permissions of the IAM role


def _validate_consumer(AwsAccountId, region, consumerType, consumerDetails):
    if consumerType == ConsumerType.RedshiftRole.value:
        pass
        # TODO: Validate Redshift role
    else:
        pass
        # TODO validate Redshift infra --> already done, pass


def _session():
    return get_context().db_engine.scoped_session()
