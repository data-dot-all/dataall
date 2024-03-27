import json
import logging
import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper
from dataall.base.utils import Parameter
from dataall.core.environment.db.environment_models import Environment
from dataall.core.environment.services.managed_iam_policies import PolicyManager
from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.environment.api.enums import EnvironmentPermission
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.core.stacks.api import stack_helper
from dataall.core.stacks.db.stack_repositories import Stack
from dataall.core.vpc.services.vpc_service import VpcService
from dataall.core.permissions import permissions
from dataall.base.feature_toggle_checker import is_feature_enabled
from dataall.core.organizations.api.resolvers import Context, exceptions, get_organization

log = logging.getLogger()


def get_trust_account(context: Context, source, **kwargs):
    current_account = SessionHelper.get_account()
    print('current_account  = ', current_account)
    return current_account


def create_environment(context: Context, source, input={}):
    env = EnvironmentService.create_environment(
        uri=input.get('organizationUri'),
        data=input,
    )

    with context.engine.scoped_session() as session:
        Stack.create_stack(
            session=session,
            environment_uri=env.environmentUri,
            target_type='environment',
            target_uri=env.environmentUri
        )
    stack_helper.deploy_stack(targetUri=env.environmentUri)

    return env


def update_environment(context: Context, source, environmentUri: str = None, input: dict = None):
    environment, previous_resource_prefix = EnvironmentService.update_environment(
        uri=environmentUri,
        data=input,
    )

    if EnvironmentResourceManager.deploy_updated_stack(previous_resource_prefix, environment, data=input):
        stack_helper.deploy_stack(targetUri=environment.environmentUri)

    return environment


def invite_group(context: Context, source, input):
    environment, environment_group = EnvironmentService.invite_group(uri=input['environmentUri'], data=input)

    stack_helper.deploy_stack(targetUri=environment.environmentUri)

    return environment


def add_consumption_role(context: Context, source, input):
    return EnvironmentService.add_consumption_role(uri=input['environmentUri'], data=input)


def update_group_permissions(context, source, input):
    environment = EnvironmentService.update_group_permissions(uri=input['environmentUri'], data=input)

    stack_helper.deploy_stack(targetUri=environment.environmentUri)

    return environment


def remove_group(context: Context, source, environmentUri=None, groupUri=None):
    environment = EnvironmentService.remove_group(
        uri=environmentUri,
        group=groupUri,
    )

    stack_helper.deploy_stack(targetUri=environment.environmentUri)

    return environment


def remove_consumption_role(context: Context, source, environmentUri=None, consumptionRoleUri=None):
    return EnvironmentService.remove_consumption_role(
        uri=consumptionRoleUri,
        env_uri=environmentUri,
    )


def update_consumption_role(context: Context, source, environmentUri=None, consumptionRoleUri=None, input={}):
    return EnvironmentService.update_consumption_role(
        uri=consumptionRoleUri,
        env_uri=environmentUri,
        data=input,
    )


def list_environment_invited_groups(context: Context, source, environmentUri=None, filter=None):
    return EnvironmentService.paginated_environment_invited_groups(
        uri=environmentUri,
        data=filter if filter else {},
    )


def list_environment_groups(context: Context, source, environmentUri=None, filter=None):
    return EnvironmentService.paginated_user_environment_groups(
        uri=environmentUri,
        data=filter if filter else {},
    )


def list_all_environment_groups(context: Context, source, environmentUri=None, filter=None):
    return EnvironmentService.paginated_all_environment_groups(
        uri=environmentUri,
        data=filter if filter else {},
    )


def list_environment_consumption_roles(context: Context, source, environmentUri=None, filter=None):
    return EnvironmentService.paginated_user_environment_consumption_roles(
        uri=environmentUri,
        data=filter if filter else {},
    )


def list_all_environment_consumption_roles(context: Context, source, environmentUri=None, filter=None):
    return EnvironmentService.paginated_all_environment_consumption_roles(
        uri=environmentUri,
        data=filter if filter else {},
    )


def list_environment_group_invitation_permissions(
        context: Context,
        source,
):
    with context.engine.scoped_session() as session:
        return EnvironmentService.list_group_invitation_permissions()


def list_environments(context: Context, source, filter=None):
    return EnvironmentService.paginated_user_environments(
        data=filter if filter else {})


def list_valid_environments(context: Context, source, filter=None):
    return EnvironmentService.list_valid_user_environments(
        data=filter if filter else {})


def list_groups(context: Context, source, filter=None):
    return EnvironmentService.paginated_user_groups(
        data=filter if filter else {})


def list_consumption_roles(context: Context, source, environmentUri=None, filter=None):
    return EnvironmentService.paginated_user_consumption_roles(
        data=filter if filter else {})


def list_environment_networks(context: Context, source, environmentUri=None, filter=None):
    return VpcService.paginated_environment_networks(
        uri=environmentUri,
        data=filter if filter else {}
    )


def get_parent_organization(context: Context, source, **kwargs):
    org = get_organization(context, source, organizationUri=source.organizationUri)
    return org


def get_policies(context: Context, source, **kwargs):
    environment = EnvironmentService.get_environment_by_uri(uri=source.environmentUri)
    return PolicyManager(
        role_name=source.IAMRoleName,
        environmentUri=environment.environmentUri,
        account=environment.AwsAccountId,
        resource_prefix=environment.resourcePrefix,
    ).get_all_policies()


def resolve_environment_networks(context: Context, source, **kwargs):
    return VpcService.get_environment_networks(environment_uri=source.environmentUri)


def get_environment(context: Context, source, environmentUri: str = None):
    return EnvironmentService.check_permissions_and_get_environment_by_uri(uri=environmentUri)


def resolve_user_role(context: Context, source: Environment):
    return EnvironmentService.resolve_user_role(source.owner, source.SamlGroupName, source.environmentUri)


def list_environment_group_permissions(context, source, environmentUri: str = None, groupUri: str = None):
    return EnvironmentService.list_group_permissions(uri=environmentUri, group_uri=groupUri)


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

    return EnvironmentService.get_environment_assume_role_url(environmentUri, groupUri)


@is_feature_enabled('core.features.env_aws_actions')
def generate_environment_access_token(context, source, environmentUri: str = None, groupUri: str = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=environmentUri,
            permission_name=permissions.CREDENTIALS_ENVIRONMENT,
        )

    return EnvironmentService.generate_environment_access_token(environmentUri, groupUri)


def get_environment_stack(context: Context, source: Environment, **kwargs):
    return stack_helper.get_stack_with_cfn_resources(
        targetUri=source.environmentUri,
        environmentUri=source.environmentUri,
    )


def delete_environment(context: Context, source, environmentUri: str = None, deleteFromAWS: bool = False):
    session_response, environment = EnvironmentService.delete_environment(uri=environmentUri)

    if deleteFromAWS:
        stack_helper.delete_stack(
            target_uri=environmentUri,
            accountid=environment.AwsAccountId,
            cdk_role_arn=environment.CDKRoleArn,
            region=environment.region,
        )

    return True


def enable_subscriptions(context: Context, source, environmentUri: str = None, input: dict = None):
    EnvironmentService.enable_subscriptions(
        environmentUri,
        username=context.username,
        groups=context.groups,
        producersTopicArn=input.get('producersTopicArn'),
    )

    stack_helper.deploy_stack(targetUri=environmentUri)
    return True


def disable_subscriptions(context: Context, source, environmentUri: str = None):
    EnvironmentService.disable_subscriptions(
        environmentUri, username=context.username, groups=context.groups
    )
    stack_helper.deploy_stack(targetUri=environmentUri)
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
                config=Config(signature_version='s3v4', s3={'addressing_style': 'virtual'}),
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
            log.error(f'Failed to get presigned URL for pivot role template due to: {e}')
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
                config=Config(signature_version='s3v4', s3={'addressing_style': 'virtual'}),
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
            log.error(f'Failed to get presigned URL for CDK Exec role template due to: {e}')
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

    return EnvironmentService.get_environment_by_uri(uri=source.environmentUri)


def resolve_parameters(context, source: Environment, **kwargs):
    """Resolves a parameters for the environment"""
    if not source:
        return None

    return EnvironmentService.get_environment_parameters(source.environmentUri)
