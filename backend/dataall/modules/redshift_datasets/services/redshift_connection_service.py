import logging

from dataall.base.context import get_context
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.permissions.services.group_policy_service import GroupPolicyService
from dataall.core.environment.services.environment_service import EnvironmentService


from dataall.modules.redshift_datasets.services.redshift_dataset_permissions import (
    MANAGE_REDSHIFT_DATASETS,
    IMPORT_REDSHIFT_DATASET
)
from dataall.modules.redshift_datasets.services.redshift_connection_permissions import (
    REDSHIFT_CONNECTION_ALL,
    DELETE_REDSHIFT_CONNECTION,
    UPDATE_REDSHIFT_CONNECTION,
    GET_REDSHIFT_CONNECTION,
)
from dataall.modules.redshift_datasets.db.redshift_dataset_models import RedshiftConnection


log = logging.getLogger(__name__)


class RedshiftConnectionService:
    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(IMPORT_REDSHIFT_DATASET)
    @GroupPolicyService.has_group_permission(IMPORT_REDSHIFT_DATASET)
    def create_redshift_connection(uri, admin_group, data: dict) -> RedshiftConnection:
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)
            connection = RedshiftConnection(
                name=data.get('name'),
                environmentUri=environment.environmentUri,
                SamlGroupName=admin_group,
                connectionName=data.get('connectionName'),
                connectionType=data.get('connectionType'),
                redshiftType=data.get('redshiftType'),
                clusterId=data.get('clusterId', ''),
                nameSpaceId=data.get('nameSpaceId', ''),
                workgroupId=data.get('workgroupId', ''),
                redshiftUser=data.get('redshiftUser', ''),
                secretArn=data.get('secretArn', ''),
            )
            session.add(connection)
            session.commit()

            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=connection.SamlGroupName,
                permissions=REDSHIFT_CONNECTION_ALL,
                resource_uri=connection.connectionUri,
                resource_type=RedshiftConnection.__name__,
            )
            return connection

    @staticmethod
    @ResourcePolicyService.has_resource_permission(DELETE_REDSHIFT_CONNECTION)
    def delete_redshift_connection(uri) -> bool:
        context = get_context()
        with (context.db_engine.scoped_session() as session):
            connection = RedshiftConnection.get_by_uri(session, uri)
            ResourcePolicyService.delete_resource_policy(
                session=session,
                resource_uri=connection.connectionUri,
                group=connection.SamlGroupName,
            )
            session.delete(connection)
            session.commit()
        return True