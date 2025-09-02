import logging

from dataall.base.context import get_context
from dataall.base.db import exceptions
from dataall.base.db.exceptions import ResourceUnauthorized
from dataall.core.permissions.services.group_policy_service import GroupPolicyService
from dataall.core.environment.db.environment_repositories import EnvironmentRepository
from dataall.core.activity.db.activity_models import Activity
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.vpc.db.vpc_repositories import VpcRepository
from dataall.core.vpc.db.vpc_models import Vpc
from dataall.core.permissions.services.network_permissions import NETWORK_ALL, DELETE_NETWORK, GET_NETWORK
from dataall.core.permissions.services.environment_permissions import CREATE_NETWORK
from dataall.core.permissions.services.tenant_permissions import MANAGE_ENVIRONMENTS

log = logging.getLogger(__name__)


def _session():
    return get_context().db_engine.scoped_session()


class VpcService:
    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(CREATE_NETWORK)
    @GroupPolicyService.has_group_permission(CREATE_NETWORK)
    def create_network(uri: str, admin_group: str, data: dict):
        with _session() as session:
            username = get_context().username
            vpc = VpcRepository.find_vpc_by_id_environment(session=session, vpc_id=data['vpcId'], environment_uri=uri)

            if vpc:
                raise exceptions.ResourceAlreadyExists(
                    action=CREATE_NETWORK,
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
                tags=data.get('tags', []),
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

            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=vpc.SamlGroupName,
                permissions=NETWORK_ALL,
                resource_uri=vpc.vpcUri,
                resource_type=Vpc.__name__,
            )

            if environment.SamlGroupName != vpc.SamlGroupName:
                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    group=environment.SamlGroupName,
                    permissions=NETWORK_ALL,
                    resource_uri=vpc.vpcUri,
                    resource_type=Vpc.__name__,
                )

            return vpc

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_ENVIRONMENTS)
    @ResourcePolicyService.has_resource_permission(DELETE_NETWORK)
    def delete_network(uri):
        with _session() as session:
            vpc = VpcRepository.get_vpc_by_uri(session=session, vpc_uri=uri)
            ResourcePolicyService.delete_resource_policy(session=session, resource_uri=uri, group=vpc.SamlGroupName)
            return VpcRepository.delete_network(session=session, uri=uri)

    @staticmethod
    def get_environment_networks(environment_uri):
        with _session() as session:
            nets = []
            all_nets = VpcRepository.get_environment_networks(session=session, environment_uri=environment_uri)
            for net in all_nets:
                try:
                    ResourcePolicyService.check_user_resource_permission(
                        session=session,
                        username=get_context().username,
                        groups=get_context().groups,
                        resource_uri=net.vpcUri,
                        permission_name=GET_NETWORK,
                    )
                except ResourceUnauthorized as exc:
                    log.info(exc)
                else:
                    nets += net
            return nets
