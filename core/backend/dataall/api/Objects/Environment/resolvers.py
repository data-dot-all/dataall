import json
import logging
import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from sqlalchemy import and_

from ..Organization.resolvers import *
from ..Stack import stack_helper
from ...constants import *
from ....aws.handlers.sts import SessionHelper
from ....aws.handlers.quicksight import Quicksight
from ....aws.handlers.cloudformation import CloudFormation
from ....db import exceptions, permissions
from ....db.api import Environment, ResourcePolicy, Stack
from ....utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)

log = logging.getLogger()


def get_trust_account(context: Context, source, **kwargs):
    current_account = SessionHelper.get_account()
    print('current_account  = ', current_account)
    return current_account


def check_environment(context: Context, source, input=None):
    ENVNAME = os.environ.get('envname', 'local')
    if ENVNAME == 'pytest':
        return 'CdkRoleName'
    account = input.get('AwsAccountId')
    region = input.get('region')
    cdk_role_name = CloudFormation.check_existing_cdk_toolkit_stack(AwsAccountId=account, region=region)

    if input.get('dashboardsEnabled'):
        existing_quicksight = Quicksight.check_quicksight_enterprise_subscription(AwsAccountId=account)

    return cdk_role_name


def create_environment(context: Context, source, input=None):
    if input.get('SamlGroupName') and input.get('SamlGroupName') not in context.groups:
        raise exceptions.UnauthorizedOperation(
            action=permissions.LINK_ENVIRONMENT,
            message=f'User: {context.username} is not a member of the group {input["SamlGroupName"]}',
        )

    with context.engine.scoped_session() as session:
        cdk_role_name = check_environment(context, source, input=input)
        input['cdk_role_name'] = cdk_role_name
        env = Environment.create_environment(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input.get('organizationUri'),
            data=input,
            check_perm=True,
        )
        Stack.create_stack(
            session=session,
            environment_uri=env.environmentUri,
            target_type='environment',
            target_uri=env.environmentUri,
            target_label=env.label,
        )
    stack_helper.deploy_stack(context, targetUri=env.environmentUri)
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

        environment = db.api.Environment.get_environment_by_uri(session, environmentUri)
        previous_resource_prefix = environment.resourcePrefix

        environment = db.api.Environment.update_environment(
            session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            data=input,
            check_perm=True,
        )
        if input.get('dashboardsEnabled') or (
            environment.resourcePrefix != previous_resource_prefix
        ):
            stack_helper.deploy_stack(
                context=context, targetUri=environment.environmentUri
            )
    return environment


def invite_group(context: Context, source, input):
    with context.engine.scoped_session() as session:
        environment, environment_group = db.api.Environment.invite_group(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input['environmentUri'],
            data=input,
            check_perm=True,
        )

    stack_helper.deploy_stack(context=context, targetUri=environment.environmentUri)

    return environment


def update_group_permissions(context, source, input):
    with context.engine.scoped_session() as session:
        environment = db.api.Environment.update_group_permissions(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input['environmentUri'],
            data=input,
            check_perm=True,
        )

    stack_helper.deploy_stack(context=context, targetUri=environment.environmentUri)

    return environment


def remove_group(context: Context, source, environmentUri=None, groupUri=None):
    with context.engine.scoped_session() as session:
        environment = db.api.Environment.remove_group(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            data={'groupUri': groupUri},
            check_perm=True,
        )

    stack_helper.deploy_stack(context=context, targetUri=environment.environmentUri)

    return environment


def list_environment_invited_groups(
    context: Context, source, environmentUri=None, filter=None
):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Environment.paginated_environment_invited_groups(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            data=filter,
            check_perm=True,
        )


def list_environment_groups(context: Context, source, environmentUri=None, filter=None):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Environment.paginated_user_environment_groups(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            data=filter,
            check_perm=True,
        )


def list_all_environment_groups(
    context: Context, source, environmentUri=None, filter=None
):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Environment.paginated_all_environment_groups(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            data=filter,
            check_perm=True,
        )


def list_environment_group_invitation_permissions(
    context: Context,
    source,
    environmentUri=None,
):
    with context.engine.scoped_session() as session:
        return db.api.Environment.list_group_invitation_permissions(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
        )


def list_environments(context: Context, source, filter=None):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Environment.paginated_user_environments(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )


def list_environment_networks(
    context: Context, source, environmentUri=None, filter=None
):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Environment.paginated_environment_networks(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            data=filter,
            check_perm=True,
        )


def get_parent_organization(context: Context, source, **kwargs):
    org = get_organization(context, source, organizationUri=source.organizationUri)
    return org


def resolve_vpc_list(context: Context, source, **kwargs):
    with context.engine.scoped_session() as session:
        return db.api.Vpc.get_environment_vpc_list(
            session=session, environment_uri=source.environmentUri
        )


def get_environment(context: Context, source, environmentUri: str = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=environmentUri,
            permission_name=permissions.GET_ENVIRONMENT,
        )
        environment = db.api.Environment.get_environment_by_uri(session, environmentUri)
        return environment


def resolve_user_role(context: Context, source: models.Environment):
    if source.owner == context.username:
        return EnvironmentPermission.Owner.value
    elif source.SamlGroupName in context.groups:
        return EnvironmentPermission.Admin.value
    else:
        with context.engine.scoped_session() as session:
            env_group = (
                session.query(models.EnvironmentGroup)
                .filter(
                    and_(
                        models.EnvironmentGroup.environmentUri == source.environmentUri,
                        models.EnvironmentGroup.groupUri.in_(context.groups),
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
        return db.api.Environment.list_group_permissions(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            data={'groupUri': groupUri},
            check_perm=True,
        )


def list_datasets_created_in_environment(
    context: Context, source, environmentUri: str = None, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Environment.paginated_environment_datasets(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            data=filter,
            check_perm=True,
        )


def list_shared_with_environment_data_items(
    context: Context, source, environmentUri: str = None, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Environment.paginated_shared_with_environment_datasets(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            data=filter,
            check_perm=True,
        )


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
        env_group: models.EnvironmentGroup = (
            session.query(models.EnvironmentGroup)
            .filter(
                models.EnvironmentGroup.environmentUri == environment.environmentUri,
                models.EnvironmentGroup.groupUri == groupUri,
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
        environment = db.api.Environment.get_environment_by_uri(session, environmentUri)
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
        environment = db.api.Environment.get_environment_by_uri(session, environmentUri)
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


def get_environment_stack(context: Context, source: models.Environment, **kwargs):
    return stack_helper.get_stack_with_cfn_resources(
        context=context,
        targetUri=source.environmentUri,
        environmentUri=source.environmentUri,
    )


def delete_environment(
    context: Context, source, environmentUri: str = None, deleteFromAWS: bool = False
):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=environmentUri,
            permission_name=permissions.DELETE_ENVIRONMENT,
        )
        environment = db.api.Environment.get_environment_by_uri(session, environmentUri)

        db.api.Environment.delete_environment(
            session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            data={'environment': environment},
            check_perm=True,
        )

    if deleteFromAWS:
        stack_helper.delete_stack(
            context=context,
            target_uri=environmentUri,
            accountid=environment.AwsAccountId,
            cdk_role_arn=environment.CDKRoleArn,
            region=environment.region,
            target_type='environment',
        )

    return True


def list_environment_redshift_clusters(
    context: Context, source, environmentUri: str = None, filter: dict = None
):
    if not filter:
        filter = dict()
    with context.engine.scoped_session() as session:
        return Environment.paginated_environment_redshift_clusters(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            data=filter,
            check_perm=True,
        )


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
        environment = db.api.Environment.get_environment_by_uri(session, environmentUri)
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
        stack_helper.deploy_stack(context=context, targetUri=environment.environmentUri)
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
        environment = db.api.Environment.get_environment_by_uri(session, environmentUri)

        environment.subscriptionsConsumersTopicName = None
        environment.subscriptionsConsumersTopicImported = False
        environment.subscriptionsProducersTopicName = None
        environment.subscriptionsProducersTopicImported = False
        environment.subscriptionsEnabled = False
        session.commit()
        stack_helper.deploy_stack(context=context, targetUri=environment.environmentUri)
        return True


def get_pivot_role_template(context: Context, source, organizationUri=None):
    from ....utils import Parameter

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
                message='Pivot role name could not be found on AWS Secretsmanager',
            )
        return pivot_role_name
