from dataall.base.context import get_context
from dataall.base.db import exceptions
from dataall.core.permissions import permissions
from dataall.core.permissions.permission_checker import has_resource_permission, has_tenant_permission
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.core.environment.env_permission_checker import has_group_permission
from dataall.core.environment.db.environment_repositories import EnvironmentRepository
from dataall.core.activity.db.activity_models import Activity
from dataall.core.vpc.db.vpc_repositories import VpcRepository
from dataall.core.vpc.db.vpc_models import Vpc


def _session():
    return get_context().db_engine.scoped_session()


class VpcService:
    @staticmethod
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.CREATE_NETWORK)
    @has_group_permission(permissions.CREATE_NETWORK)
    def create_network(uri: str, admin_group: str, data: dict):
        with _session() as session:
            username = get_context().username
            vpc = VpcRepository.find_vpc_by_id_environment(session=session, vpc_id=data['vpcId'], environment_uri=uri)

            if vpc:
                raise exceptions.ResourceAlreadyExists(
                    action=permissions.CREATE_NETWORK,
                    message=f'Vpc {data["vpcId"]} is already associated to environment {uri}',
                )

            environment = EnvironmentRepository.get_environment_by_uri(session, uri)
            vpc = Vpc(
                environmentUri=environment.environmentUri,
                region=environment.region,
                AwsAccountId=environment.AwsAccountId,
                VpcId=data['vpcId'],
                privateSubnetIds=data.get('privateSubnetIds', []),
                publicSubnetIds=data.get('publicSubnetIds', []),
                SamlGroupName=data['SamlGroupName'],
                owner=username,
                label=data['label'],
                name=data['label'],
                default=data.get('default', False),
            )
            VpcRepository.save_network(session, vpc)

            activity = Activity(
                action='NETWORK:CREATE',
                label='NETWORK:CREATE',
                owner=username,
                summary=f'{username} created network {vpc.label} in {environment.label}',
                targetUri=vpc.vpcUri,
                targetType='Vpc',
            )
            session.add(activity)

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=vpc.SamlGroupName,
                permissions=permissions.NETWORK_ALL,
                resource_uri=vpc.vpcUri,
                resource_type=Vpc.__name__,
            )

            if environment.SamlGroupName != vpc.SamlGroupName:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=environment.SamlGroupName,
                    permissions=permissions.NETWORK_ALL,
                    resource_uri=vpc.vpcUri,
                    resource_type=Vpc.__name__,
                )

            return vpc

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_ENVIRONMENTS)
    @has_resource_permission(permissions.DELETE_NETWORK)
    def delete_network(uri):
        with _session() as session:
            vpc = VpcRepository.get_vpc_by_uri(session=session, vpc_uri=uri)
            ResourcePolicy.delete_resource_policy(session=session, resource_uri=uri, group=vpc.SamlGroupName)
            return VpcRepository.delete_network(session=session, uri=uri)

    @staticmethod
    def get_environment_networks(environment_uri):
        with _session() as session:
            return VpcRepository.get_environment_networks(session=session, environment_uri=environment_uri)
