import json
import logging
import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from sqlalchemy import and_, exc

from dataall.base.aws.iam import IAM
from dataall.base.aws.parameter_store import ParameterStoreManager
from dataall.base.aws.sts import SessionHelper
from dataall.base.utils import Parameter
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.environment.api.enums import EnvironmentPermission
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.core.stacks.api import stack_helper
from dataall.core.stacks.aws.cloudformation import CloudFormation
from dataall.core.stacks.db.stack_repositories import Stack
from dataall.core.vpc.db.vpc_repositories import Vpc
from dataall.base.aws.ec2_client import EC2
from dataall.base.db import exceptions
from dataall.core.permissions import permissions
from dataall.base.feature_toggle_checker import is_feature_enabled
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from dataall.core.organizations.api.resolvers import *

log = logging.getLogger()


def get_trust_account(context: Context, source, **kwargs):
    current_account = SessionHelper.get_account()
    print('current_account  = ', current_account)
    return current_account


def get_pivot_role_as_part_of_environment(context: Context, source, **kwargs):
    ssm_param = ParameterStoreManager.get_parameter_value(region=os.getenv('AWS_REGION', 'eu-west-1'), parameter_path=f"/dataall/{os.getenv('envname', 'local')}/pivotRole/enablePivotRoleAutoCreate")
    return True if ssm_param == "True" else False


def check_environment(context: Context, source, account_id, region, data):
    """ Checks necessary resources for environment deployment.
    - Check CDKToolkit exists in Account assuming cdk_look_up_role
    - Check Pivot Role exists in Account if pivot_role_as_part_of_environment is False
    Args:
        input: environment creation input
    """
    pivot_role_as_part_of_environment = get_pivot_role_as_part_of_environment(context, source)
    log.info(f"Creating environment. Pivot role as part of environment = {pivot_role_as_part_of_environment}")
    ENVNAME = os.environ.get('envname', 'local')
    if ENVNAME == 'pytest':
        return 'CdkRoleName'

    cdk_look_up_role_arn = SessionHelper.get_cdk_look_up_role_arn(
        accountid=account_id, region=region
    )
    cdk_role_name = CloudFormation.check_existing_cdk_toolkit_stack(
        AwsAccountId=account_id, region=region
    )
    if not pivot_role_as_part_of_environment:
        log.info("Check if PivotRole exist in the account")
        pivot_role_arn = SessionHelper.get_delegation_role_arn(accountid=account_id)
        role = IAM.get_role(account_id=account_id, role_arn=pivot_role_arn, role=cdk_look_up_role_arn)
        if not role:
            raise exceptions.AWSResourceNotFound(
                action='CHECK_PIVOT_ROLE',
                message='Pivot Role has not been created in the Environment AWS Account',
            )
    mlStudioEnabled = None
    for parameter in data.get("parameters", []):
        if parameter['key'] == 'mlStudiosEnabled':
            mlStudioEnabled = parameter['value']

    if mlStudioEnabled and data.get("vpcId", None) and data.get("subnetIds", []):
        log.info("Check if ML Studio VPC Exists in the Account")
        EC2.check_vpc_exists(
            AwsAccountId=account_id,
            region=region,
            role=cdk_look_up_role_arn,
            vpc_id=data.get("vpcId", None),
            subnet_ids=data.get('subnetIds', []),
        )

    return cdk_role_name


def create_environment(context: Context, source, input={}):
    if input.get('SamlGroupName') and input.get('SamlGroupName') not in context.groups:
        raise exceptions.UnauthorizedOperation(
            action=permissions.LINK_ENVIRONMENT,
            message=f'User: {context.username} is not a member of the group {input["SamlGroupName"]}',
        )

    with context.engine.scoped_session() as session:
        cdk_role_name = check_environment(context, source,
                                          account_id=input.get('AwsAccountId'),
                                          region=input.get('region'),
                                          data=input
                                          )

        input['cdk_role_name'] = cdk_role_name
        env = EnvironmentService.create_environment(
            session=session,
            uri=input.get('organizationUri'),
            data=input,
        )
        Stack.create_stack(
            session=session,
            environment_uri=env.environmentUri,
            target_type='environment',
            target_uri=env.environmentUri,
            target_label=env.label,
        )
    stack_helper.deploy_stack(targetUri=env.environmentUri)
    env.userRoleInEnvironment = EnvironmentPermission.Owner.value
    return env


def update_environment(
    context: Context, source, environmentUri: str = None, input: dict = None
):
    if input.get('SamlGroupName') and input.get('SamlGroupName') not in context.groups:
        raise exceptions.UnauthorizedOperation(
            action=permissions.LINK_ENVIRONMENT,
            message=f'User: {context.username} is not part of the group {input["SamlGroupName"]}',
        )

    with context.engine.scoped_session() as session:

        environment = EnvironmentService.get_environment_by_uri(session, environmentUri)
        cdk_role_name = check_environment(context, source,
                                          account_id=environment.AwsAccountId,
                                          region=environment.region,
                                          data=input
                                          )

        previous_resource_prefix = environment.resourcePrefix

        environment = EnvironmentService.update_environment(
            session,
            uri=environmentUri,
            data=input,
        )

        if EnvironmentResourceManager.deploy_updated_stack(session, previous_resource_prefix, environment, data=input):
            stack_helper.deploy_stack(targetUri=environment.environmentUri)

    return environment


def invite_group(context: Context, source, input):
    with context.engine.scoped_session() as session:
        environment, environment_group = EnvironmentService.invite_group(
            session=session,
            uri=input['environmentUri'],
            data=input,
        )

    stack_helper.deploy_stack(targetUri=environment.environmentUri)

    return environment


def add_consumption_role(context: Context, source, input):
    with context.engine.scoped_session() as session:
        env = EnvironmentService.get_environment_by_uri(session, input['environmentUri'])
        role = IAM.get_role(env.AwsAccountId, input['IAMRoleArn'])
        if not role:
            raise exceptions.AWSResourceNotFound(
                action='ADD_CONSUMPTION_ROLE',
                message=f"{input['IAMRoleArn']} does not exist in this account",
            )
        consumption_role = EnvironmentService.add_consumption_role(
            session=session,
            uri=input['environmentUri'],
            data=input,
        )

    return consumption_role


def update_group_permissions(context, source, input):
    with context.engine.scoped_session() as session:
        environment = EnvironmentService.update_group_permissions(
            session=session,
            uri=input['environmentUri'],
            data=input,
        )

    stack_helper.deploy_stack(targetUri=environment.environmentUri)

    return environment


def remove_group(context: Context, source, environmentUri=None, groupUri=None):
    with context.engine.scoped_session() as session:
        environment = EnvironmentService.remove_group(
            session=session,
            uri=environmentUri,
            group=groupUri,
        )

    stack_helper.deploy_stack(targetUri=environment.environmentUri)

    return environment


def remove_consumption_role(context: Context, source, environmentUri=None, consumptionRoleUri=None):
    with context.engine.scoped_session() as session:
        status = EnvironmentService.remove_consumption_role(
            session=session,
            uri=consumptionRoleUri,
            env_uri=environmentUri,
        )

    return status


def update_consumption_role(context: Context, source, environmentUri=None, consumptionRoleUri=None, input={}):
    with context.engine.scoped_session() as session:
        status = EnvironmentService.update_consumption_role(
            session=session,
            uri=consumptionRoleUri,
            env_uri=environmentUri,
            input=input,
        )
    return status


def list_environment_invited_groups(
    context: Context, source, environmentUri=None, filter=None
):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return EnvironmentService.paginated_environment_invited_groups(
            session=session,
            uri=environmentUri,
            data=filter,
        )


def list_environment_groups(context: Context, source, environmentUri=None, filter=None):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return EnvironmentService.paginated_user_environment_groups(
            session=session,
            uri=environmentUri,
            data=filter,
        )


def list_all_environment_groups(
    context: Context, source, environmentUri=None, filter=None
):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return EnvironmentService.paginated_all_environment_groups(
            session=session,
            uri=environmentUri,
            data=filter,
        )


def list_environment_consumption_roles(
    context: Context, source, environmentUri=None, filter=None
):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return EnvironmentService.paginated_user_environment_consumption_roles(
            session=session,
            uri=environmentUri,
            data=filter,
        )


def list_all_environment_consumption_roles(
    context: Context, source, environmentUri=None, filter=None
):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return EnvironmentService.paginated_all_environment_consumption_roles(
            session=session,
            uri=environmentUri,
            data=filter,
        )


def list_environment_group_invitation_permissions(
    context: Context,
    source,
    environmentUri=None,
):
    with context.engine.scoped_session() as session:
        return EnvironmentService.list_group_invitation_permissions(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
        )


def list_environments(context: Context, source, filter=None):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return EnvironmentService.paginated_user_environments(session, filter)


def list_valid_environments(context: Context, source, filter=None):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return EnvironmentService.list_valid_user_environments(session, filter)


def list_groups(context: Context, source, filter=None):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return EnvironmentService.paginated_user_groups(session, filter)


def list_consumption_roles(
    context: Context, source, environmentUri=None, filter=None
):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return EnvironmentService.paginated_user_consumption_roles(
            session=session,
            data=filter,
        )


def list_environment_networks(
    context: Context, source, environmentUri=None, filter=None
):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return EnvironmentService.paginated_environment_networks(
            session=session,
            uri=environmentUri,
            data=filter,
        )


def get_parent_organization(context: Context, source, **kwargs):
    org = get_organization(context, source, organizationUri=source.organizationUri)
    return org


def resolve_vpc_list(context: Context, source, **kwargs):
    with context.engine.scoped_session() as session:
        return Vpc.get_environment_vpc_list(
            session=session, environment_uri=source.environmentUri
        )


def get_environment(context: Context, source, environmentUri: str = None):
    with context.engine.scoped_session() as session:
        return EnvironmentService.find_environment_by_uri(session, uri=environmentUri)


def resolve_user_role(context: Context, source: Environment):
    if source.owner == context.username:
        return EnvironmentPermission.Owner.value
    elif source.SamlGroupName in context.groups:
        return EnvironmentPermission.Admin.value
    else:
        with context.engine.scoped_session() as session:
            env_group = (
                session.query(EnvironmentGroup)
                .filter(
                    and_(
                        EnvironmentGroup.environmentUri == source.environmentUri,
                        EnvironmentGroup.groupUri.in_(context.groups),
                    )
                )
                .first()
            )
            if env_group:
                return EnvironmentPermission.Invited.value
    return EnvironmentPermission.NotInvited.value


def list_environment_group_permissions(
    context, source, environmentUri: str = None, groupUri: str = None
):
    with context.engine.scoped_session() as session:
        return EnvironmentService.list_group_permissions(
            session=session,
            uri=environmentUri,
            group_uri=groupUri
        )


@is_feature_enabled('core.features.env_aws_actions')
def _get_environment_group_aws_session(
    session, username, groups, environment, groupUri=None
):
    if groupUri and groupUri not in groups:
        raise exceptions.UnauthorizedOperation(
            action='ENVIRONMENT_AWS_ACCESS',
            message=f'User: {username} is not member of the team {groupUri}',
        )
    pivot_session = SessionHelper.remote_session(environment.AwsAccountId)
    if not groupUri:
        if environment.SamlGroupName in groups:
            aws_session = SessionHelper.get_session(
                base_session=pivot_session,
                role_arn=environment.EnvironmentDefaultIAMRoleArn,
            )
        else:
            raise exceptions.UnauthorizedOperation(
                action='ENVIRONMENT_AWS_ACCESS',
                message=f'User: {username} is not member of the environment admins team {environment.SamlGroupName}',
            )
    else:
        env_group: EnvironmentGroup = (
            session.query(EnvironmentGroup)
            .filter(
                EnvironmentGroup.environmentUri == environment.environmentUri,
                EnvironmentGroup.groupUri == groupUri,
            )
            .first()
        )
        if not env_group:
            raise exceptions.UnauthorizedOperation(
                action='ENVIRONMENT_AWS_ACCESS',
                message=f'Team {groupUri} is not invited to the environment {environment.name}',
            )
        else:
            aws_session = SessionHelper.get_session(
                base_session=pivot_session,
                role_arn=env_group.environmentIAMRoleArn,
            )
        if not aws_session:
            raise exceptions.AWSResourceNotFound(
                action='ENVIRONMENT_AWS_ACCESS',
                message=f'Failed to start an AWS session on environment {environment.AwsAccountId}',
            )
    return aws_session


@is_feature_enabled('core.features.env_aws_actions')
def get_environment_assume_role_url(
    context: Context,
    source,
    environmentUri: str = None,
    groupUri: str = None,
):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=environmentUri,
            permission_name=permissions.CREDENTIALS_ENVIRONMENT,
        )
        environment = EnvironmentService.get_environment_by_uri(session, environmentUri)
        url = SessionHelper.get_console_access_url(
            _get_environment_group_aws_session(
                session=session,
                username=context.username,
                groups=context.groups,
                environment=environment,
                groupUri=groupUri,
            ),
            region=environment.region,
        )
    return url


@is_feature_enabled('core.features.env_aws_actions')
def generate_environment_access_token(
    context, source, environmentUri: str = None, groupUri: str = None
):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=environmentUri,
            permission_name=permissions.CREDENTIALS_ENVIRONMENT,
        )
        environment = EnvironmentService.get_environment_by_uri(session, environmentUri)
        c = _get_environment_group_aws_session(
            session=session,
            username=context.username,
            groups=context.groups,
            environment=environment,
            groupUri=groupUri,
        ).get_credentials()
        credentials = {
            'AccessKey': c.access_key,
            'SessionKey': c.secret_key,
            'sessionToken': c.token,
        }
    return json.dumps(credentials)


def get_environment_stack(context: Context, source: Environment, **kwargs):
    return stack_helper.get_stack_with_cfn_resources(
        targetUri=source.environmentUri,
        environmentUri=source.environmentUri,
    )


def delete_environment(
    context: Context, source, environmentUri: str = None, deleteFromAWS: bool = False
):
    with context.engine.scoped_session() as session:
        environment = EnvironmentService.get_environment_by_uri(session, environmentUri)
        EnvironmentService.delete_environment(
            session,
            uri=environmentUri,
            environment=environment
        )

    if deleteFromAWS:
        stack_helper.delete_stack(
            target_uri=environmentUri,
            accountid=environment.AwsAccountId,
            cdk_role_arn=environment.CDKRoleArn,
            region=environment.region,
        )

    return True


def enable_subscriptions(
    context: Context, source, environmentUri: str = None, input: dict = None
):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=environmentUri,
            permission_name=permissions.ENABLE_ENVIRONMENT_SUBSCRIPTIONS,
        )
        environment = EnvironmentService.get_environment_by_uri(session, environmentUri)
        if input.get('producersTopicArn'):
            environment.subscriptionsProducersTopicName = input.get('producersTopicArn')
            environment.subscriptionsProducersTopicImported = True

        else:
            environment.subscriptionsProducersTopicName = NamingConventionService(
                target_label=f'{environment.label}-producers-topic',
                target_uri=environment.environmentUri,
                pattern=NamingConventionPattern.DEFAULT,
                resource_prefix=environment.resourcePrefix,
            ).build_compliant_name()

        environment.subscriptionsConsumersTopicName = NamingConventionService(
            target_label=f'{environment.label}-consumers-topic',
            target_uri=environment.environmentUri,
            pattern=NamingConventionPattern.DEFAULT,
            resource_prefix=environment.resourcePrefix,
        ).build_compliant_name()
        environment.subscriptionsConsumersTopicImported = False
        environment.subscriptionsEnabled = True
        session.commit()
        stack_helper.deploy_stack(targetUri=environment.environmentUri)
        return True


def disable_subscriptions(context: Context, source, environmentUri: str = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=environmentUri,
            permission_name=permissions.ENABLE_ENVIRONMENT_SUBSCRIPTIONS,
        )
        environment = EnvironmentService.get_environment_by_uri(session, environmentUri)

        environment.subscriptionsConsumersTopicName = None
        environment.subscriptionsConsumersTopicImported = False
        environment.subscriptionsProducersTopicName = None
        environment.subscriptionsProducersTopicImported = False
        environment.subscriptionsEnabled = False
        session.commit()
        stack_helper.deploy_stack(targetUri=environment.environmentUri)
        return True


def get_pivot_role_template(context: Context, source, organizationUri=None):
    from dataall.base.utils import Parameter

    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=organizationUri,
            permission_name=permissions.GET_ORGANIZATION,
        )
        pivot_role_bucket = Parameter().get_parameter(
            env=os.getenv('envname', 'local'), path='s3/resources_bucket_name'
        )
        pivot_role_bucket_key = Parameter().get_parameter(
            env=os.getenv('envname', 'local'), path='s3/pivot_role_prefix'
        )
        if not pivot_role_bucket or not pivot_role_bucket_key:
            raise exceptions.AWSResourceNotFound(
                action='GET_PIVOT_ROLE_TEMPLATE',
                message='Pivot Yaml template file could not be found on Amazon S3 bucket',
            )
        try:
            s3_client = boto3.client(
                's3',
                region_name=os.getenv('AWS_REGION', 'eu-central-1'),
                config=Config(
                    signature_version='s3v4', s3={'addressing_style': 'virtual'}
                ),
            )
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params=dict(
                    Bucket=pivot_role_bucket,
                    Key=pivot_role_bucket_key,
                ),
                ExpiresIn=15 * 60,
            )
            return presigned_url
        except ClientError as e:
            log.error(
                f'Failed to get presigned URL for pivot role template due to: {e}'
            )
            raise e


def get_cdk_exec_policy_template(context: Context, source, organizationUri=None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=organizationUri,
            permission_name=permissions.GET_ORGANIZATION,
        )
        cdk_exec_policy_bucket = Parameter().get_parameter(
            env=os.getenv('envname', 'local'), path='s3/resources_bucket_name'
        )
        cdk_exec_policy_bucket_key = Parameter().get_parameter(
            env=os.getenv('envname', 'local'), path='s3/cdk_exec_policy_prefix'
        )
        if not cdk_exec_policy_bucket or not cdk_exec_policy_bucket_key:
            raise exceptions.AWSResourceNotFound(
                action='GET_CDK_EXEC_POLICY_TEMPLATE',
                message='CDK Exec Yaml template file could not be found on Amazon S3 bucket',
            )
        try:
            s3_client = boto3.client(
                's3',
                region_name=os.getenv('AWS_REGION', 'eu-central-1'),
                config=Config(
                    signature_version='s3v4', s3={'addressing_style': 'virtual'}
                ),
            )
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params=dict(
                    Bucket=cdk_exec_policy_bucket,
                    Key=cdk_exec_policy_bucket_key,
                ),
                ExpiresIn=15 * 60,
            )
            return presigned_url
        except ClientError as e:
            log.error(
                f'Failed to get presigned URL for CDK Exec role template due to: {e}'
            )
            raise e


def get_external_id(context: Context, source, organizationUri=None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=organizationUri,
            permission_name=permissions.GET_ORGANIZATION,
        )
        external_id = SessionHelper.get_external_id_secret()
        if not external_id:
            raise exceptions.AWSResourceNotFound(
                action='GET_EXTERNAL_ID',
                message='External Id could not be found on AWS Secretsmanager',
            )
        return external_id


def get_pivot_role_name(context: Context, source, organizationUri=None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=organizationUri,
            permission_name=permissions.GET_ORGANIZATION,
        )
        pivot_role_name = SessionHelper.get_delegation_role_name()
        if not pivot_role_name:
            raise exceptions.AWSResourceNotFound(
                action='GET_PIVOT_ROLE_NAME',
                message='Pivot role name could not be found on AWS Systems Manager - Parameter Store',
            )
        return pivot_role_name


def resolve_environment(context, source, **kwargs):
    """Resolves the environment for a environmental resource"""
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return session.query(Environment).get(source.environmentUri)


def resolve_parameters(context, source: Environment, **kwargs):
    """Resolves a parameters for the environment"""
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return EnvironmentService.get_environment_parameters(session, source.environmentUri)
