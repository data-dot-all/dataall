import json
import logging

from botocore.exceptions import ClientError

from .... import db
from ....api.context import Context
from ....aws.handlers.redshift import Redshift
from ....aws.handlers.service_handlers import Worker
from ....aws.handlers.sts import SessionHelper
from ....db import models, permissions
from ....db.api import KeyValueTag, ResourcePolicy, Stack
from ...constants import RedshiftClusterRole
from ..Stack import stack_helper

log = logging.getLogger(__name__)


def create(
    context: Context, source, environmentUri: str = None, clusterInput: dict = None
):

    with context.engine.scoped_session() as session:

        cluster = db.api.RedshiftCluster.create(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            data=clusterInput,
            check_perm=True,
        )

        log.debug(f'Create Redshift Cluster Stack: {cluster}')

        stack = Stack.create_stack(
            session=session,
            environment_uri=cluster.environmentUri,
            target_type='redshift',
            target_uri=cluster.clusterUri,
            target_label=cluster.label,
        )
        cluster.CFNStackName = stack.name if stack else None

    stack_helper.deploy_stack(context=context, targetUri=cluster.clusterUri)
    cluster.userRoleForCluster = RedshiftClusterRole.Creator.value
    return cluster


def import_cluster(context: Context, source, environmentUri: str, clusterInput: dict):

    with context.engine.scoped_session() as session:

        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=environmentUri,
            permission_name=permissions.CREATE_REDSHIFT_CLUSTER,
        )
        db.api.Environment.check_group_environment_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            group=clusterInput['SamlGroupName'],
            permission_name=permissions.CREATE_REDSHIFT_CLUSTER,
        )
        environment = db.api.Environment.get_environment_by_uri(session, environmentUri)

        aws_cluster_details = Redshift.describe_clusters(
            **{
                'accountid': environment.AwsAccountId,
                'region': environment.region,
                'cluster_id': clusterInput['clusterIdentifier'],
            }
        )

        if not aws_cluster_details:
            raise db.exceptions.AWSResourceNotFound(
                action='IMPORT_REDSHIFT_CLUSTER',
                message=f"{clusterInput['clusterIdentifier']} "
                f'not found on AWS {environment.AwsAccountId}//{environment.region}',
            )

        cluster = models.RedshiftCluster(
            environmentUri=environment.environmentUri,
            organizationUri=environment.organizationUri,
            owner=context.username,
            label=clusterInput['label'],
            description=clusterInput.get('description'),
            tags=clusterInput.get('tags'),
            region=environment.region,
            AwsAccountId=environment.AwsAccountId,
            imported=True,
            SamlGroupName=clusterInput.get('SamlGroupName', environment.SamlGroupName),
        )
        cluster = map_aws_details_to_model(
            aws_cluster_details=aws_cluster_details, cluster=cluster
        )
        session.add(cluster)
        session.commit()

        stack = models.Stack(
            targetUri=cluster.clusterUri,
            accountid=cluster.AwsAccountId,
            region=cluster.region,
            stack='redshift',
        )
        session.add(stack)
        cluster.CFNStackName = f'stack-{stack.stackUri}' if stack else None
        session.commit()

        redshift_assign_role_task = models.Task(
            targetUri=cluster.clusterUri,
            action='redshift.iam_roles.update',
        )
        session.add(redshift_assign_role_task)
        session.commit()

    log.info('Updating imported cluster iam_roles')
    Worker.queue(engine=context.engine, task_ids=[redshift_assign_role_task.taskUri])

    stack_helper.deploy_stack(context=context, targetUri=cluster.clusterUri)

    return cluster


def get_cluster(context: Context, source, clusterUri: str = None):
    with context.engine.scoped_session() as session:
        return db.api.RedshiftCluster.get_cluster(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=clusterUri,
            data=None,
            check_perm=True,
        )


def resolve_user_role(context: Context, source: models.RedshiftCluster):
    if not source:
        return None
    if context.username and source.owner == context.username:
        return RedshiftClusterRole.Creator.value
    elif context.groups and source.SamlGroupName in context.groups:
        return RedshiftClusterRole.Admin.value
    return RedshiftClusterRole.NoPermission.value


def get_cluster_status(context: Context, source: models.RedshiftCluster):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        try:
            aws_cluster = Redshift.describe_clusters(
                **{
                    'accountid': source.AwsAccountId,
                    'region': source.region,
                    'cluster_id': source.name,
                }
            )
            if aws_cluster:
                map_aws_details_to_model(aws_cluster, source)
            if not source.external_schema_created:
                task_init_db = models.Task(
                    targetUri=source.clusterUri,
                    action='redshift.cluster.init_database',
                )
                session.add(task_init_db)
                session.commit()
                Worker.queue(engine=context.engine, task_ids=[task_init_db.taskUri])

            return source.status
        except ClientError as e:
            log.error(f'Failed to retrieve cluster status due to: {e}')


def map_aws_details_to_model(aws_cluster_details, cluster):
    cluster.name = aws_cluster_details.get('ClusterIdentifier')
    cluster.status = aws_cluster_details.get('ClusterStatus')
    cluster.numberOfNodes = aws_cluster_details.get('NumberOfNodes')
    cluster.masterUsername = aws_cluster_details.get('MasterUsername')
    cluster.masterDatabaseName = aws_cluster_details.get('DBName')
    cluster.endpoint = (
        aws_cluster_details.get('Endpoint').get('Address')
        if aws_cluster_details.get('Endpoint')
        else None
    )
    cluster.port = (
        aws_cluster_details.get('Endpoint').get('Port')
        if aws_cluster_details.get('Endpoint')
        else None
    )
    cluster.subnetGroupName = aws_cluster_details.get('ClusterSubnetGroupName')
    cluster.IAMRoles = (
        [role.get('IamRoleArn') for role in aws_cluster_details.get('IamRoles')]
        if aws_cluster_details.get('IamRoles')
        else None
    )
    cluster.nodeType = aws_cluster_details.get('NodeType')
    cluster.securityGroupIds = (
        [
            vpc.get('VpcSecurityGroupId')
            for vpc in aws_cluster_details.get('VpcSecurityGroups')
        ]
        if aws_cluster_details.get('VpcSecurityGroups')
        else None
    )
    cluster.vpc = aws_cluster_details.get('VpcId')
    cluster.tags = (
        [{tag.get('Key'), tag.get('Value')} for tag in aws_cluster_details.get('tags')]
        if aws_cluster_details.get('tags')
        else None
    )
    return cluster


def get_cluster_organization(context: Context, source: models.RedshiftCluster):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        org = session.query(models.Organization).get(source.organizationUri)
    return org


def get_cluster_environment(context: Context, source: models.RedshiftCluster):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return db.api.Environment.get_environment_by_uri(session, source.environmentUri)


def delete(
    context: Context, source, clusterUri: str = None, deleteFromAWS: bool = False
):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            resource_uri=clusterUri,
            username=context.username,
            groups=context.groups,
            permission_name=permissions.DELETE_REDSHIFT_CLUSTER,
        )
        cluster = db.api.RedshiftCluster.get_redshift_cluster_by_uri(
            session, clusterUri
        )
        env: models.Environment = db.api.Environment.get_environment_by_uri(
            session, cluster.environmentUri
        )
        db.api.RedshiftCluster.delete_all_cluster_linked_objects(session, clusterUri)

        KeyValueTag.delete_key_value_tags(session, cluster.clusterUri, 'redshift')

        session.delete(cluster)

        ResourcePolicy.delete_resource_policy(
            session=session,
            resource_uri=clusterUri,
            group=cluster.SamlGroupName,
        )

    if deleteFromAWS:
        stack_helper.delete_stack(
            context=context,
            target_uri=clusterUri,
            accountid=env.AwsAccountId,
            cdk_role_arn=env.CDKRoleArn,
            region=env.region,
            target_type='redshiftcluster',
        )

    return True


def pause_cluster(context: Context, source, clusterUri: str = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            resource_uri=clusterUri,
            username=context.username,
            groups=context.groups,
            permission_name=permissions.PAUSE_REDSHIFT_CLUSTER,
        )
        cluster = db.api.RedshiftCluster.get_redshift_cluster_by_uri(
            session, clusterUri
        )
        Redshift.pause_cluster(
            **{
                'accountid': cluster.AwsAccountId,
                'region': cluster.region,
                'cluster_id': cluster.name,
            }
        )
        return True


def resume_cluster(context: Context, source, clusterUri: str = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            resource_uri=clusterUri,
            username=context.username,
            groups=context.groups,
            permission_name=permissions.RESUME_REDSHIFT_CLUSTER,
        )
        cluster = db.api.RedshiftCluster.get_redshift_cluster_by_uri(
            session, clusterUri
        )
        Redshift.resume_cluster(
            **{
                'accountid': cluster.AwsAccountId,
                'region': cluster.region,
                'cluster_id': cluster.name,
            }
        )
        return True


def reboot_cluster(context: Context, source, clusterUri: str = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            resource_uri=clusterUri,
            username=context.username,
            groups=context.groups,
            permission_name=permissions.REBOOT_REDSHIFT_CLUSTER,
        )
        cluster = db.api.RedshiftCluster.get_redshift_cluster_by_uri(
            session, clusterUri
        )
        Redshift.reboot_cluster(
            **{
                'accountid': cluster.AwsAccountId,
                'region': cluster.region,
                'cluster_id': cluster.name,
            }
        )
        return True


def get_console_access(context: Context, source, clusterUri: str = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            resource_uri=clusterUri,
            username=context.username,
            groups=context.groups,
            permission_name=permissions.GET_REDSHIFT_CLUSTER_CREDENTIALS,
        )
        cluster = db.api.RedshiftCluster.get_redshift_cluster_by_uri(
            session, clusterUri
        )
        environment = db.api.Environment.get_environment_by_uri(
            session, cluster.environmentUri
        )
        pivot_session = SessionHelper.remote_session(environment.AwsAccountId)
        aws_session = SessionHelper.get_session(
            base_session=pivot_session,
            role_arn=environment.EnvironmentDefaultIAMRoleArn,
        )
        url = SessionHelper.get_console_access_url(
            aws_session, region=cluster.region, redshiftcluster=cluster.name
        )
        return url


def add_dataset_to_cluster(
    context: Context, source, clusterUri: str = None, datasetUri: str = None
):
    with context.engine.scoped_session() as session:
        cluster = db.api.RedshiftCluster.get_redshift_cluster_by_uri(
            session, clusterUri
        )
        aws_cluster = Redshift.describe_clusters(
            **{
                'accountid': cluster.AwsAccountId,
                'region': cluster.region,
                'cluster_id': cluster.name,
            }
        )
        if aws_cluster:
            map_aws_details_to_model(aws_cluster, cluster)
        cluster, dataset = db.api.RedshiftCluster.add_dataset(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=clusterUri,
            data={'datasetUri': datasetUri},
            check_perm=True,
        )
        task = models.Task(
            targetUri=cluster.clusterUri,
            action='redshift.cluster.create_external_schema',
        )
        session.add(task)
        session.commit()

    Worker.queue(context.engine, [task.taskUri])
    return True


def remove_dataset_from_cluster(
    context: Context, source, clusterUri: str = None, datasetUri: str = None
):
    with context.engine.scoped_session() as session:
        cluster, dataset = db.api.RedshiftCluster.remove_dataset_from_cluster(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=clusterUri,
            data={'datasetUri': datasetUri},
            check_perm=True,
        )
        if dataset.environmentUri != cluster.environmentUri:
            database = f'{dataset.GlueDatabaseName}shared'
        else:
            database = dataset.GlueDatabaseName
        task = models.Task(
            targetUri=cluster.clusterUri,
            action='redshift.cluster.drop_external_schema',
            payload={'database': database},
        )
        session.add(task)
        session.commit()

    Worker.queue(context.engine, [task.taskUri])
    return True


def list_cluster_available_datasets(
    context: Context, source, clusterUri: str = None, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.RedshiftCluster.list_available_datasets(
            session,
            username=context.username,
            groups=context.groups,
            uri=clusterUri,
            data=filter,
            check_perm=True,
        )


def list_cluster_datasets(
    context: Context, source, clusterUri: str = None, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.RedshiftCluster.list_cluster_datasets(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=clusterUri,
            data=filter,
            check_perm=True,
        )


def list_available_cluster_dataset_tables(
    context: Context, source, clusterUri: str = None, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.RedshiftCluster.list_available_cluster_tables(
            session,
            username=context.username,
            groups=context.groups,
            uri=clusterUri,
            data=filter,
            check_perm=True,
        )


def list_copy_enabled_dataset_tables(
    context: Context, source, clusterUri: str = None, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.RedshiftCluster.list_copy_enabled_tables(
            session,
            username=context.username,
            groups=context.groups,
            uri=clusterUri,
            data=filter,
            check_perm=True,
        )


def get_datahubdb_credentials(context: Context, source, clusterUri: str = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            resource_uri=clusterUri,
            username=context.username,
            groups=context.groups,
            permission_name=permissions.GET_REDSHIFT_CLUSTER_CREDENTIALS,
        )
        cluster = db.api.RedshiftCluster.get_redshift_cluster_by_uri(
            session, clusterUri
        )
        creds = Redshift.get_cluster_credentials(
            **{
                'accountid': cluster.AwsAccountId,
                'region': cluster.region,
                'cluster_id': cluster.name,
                'secret_name': cluster.datahubSecret,
            }
        )
        return {
            'clusterUri': clusterUri,
            'endpoint': cluster.endpoint,
            'port': cluster.port,
            'database': cluster.databaseName,
            'user': cluster.databaseUser,
            'password': creds,
        }


def resolve_stack(context: Context, source: models.RedshiftCluster, **kwargs):
    if not source:
        return None
    return stack_helper.get_stack_with_cfn_resources(
        context=context,
        targetUri=source.clusterUri,
        environmentUri=source.environmentUri,
    )


def enable_dataset_table_copy(
    context: Context,
    source,
    clusterUri: str = None,
    datasetUri: str = None,
    tableUri: str = None,
    schema: str = None,
    dataLocation: str = None,
):
    with context.engine.scoped_session() as session:
        cluster = db.api.RedshiftCluster.get_redshift_cluster_by_uri(
            session, clusterUri
        )
        db.api.RedshiftCluster.enable_copy_table(
            session,
            username=context.username,
            groups=context.groups,
            uri=clusterUri,
            data={
                'datasetUri': datasetUri,
                'tableUri': tableUri,
                'schema': schema,
                'dataLocation': dataLocation,
            },
            check_perm=True,
        )
        log.info(
            f'Redshift copy tableUri {tableUri} starting for cluster'
            f'{cluster.name} in account {cluster.AwsAccountId}'
        )
        task = models.Task(
            action='redshift.subscriptions.copy',
            targetUri=cluster.environmentUri,
            payload={
                'datasetUri': datasetUri,
                'message': json.dumps({'clusterUri': clusterUri}),
                'tableUri': tableUri,
            },
        )
        session.add(task)
        session.commit()

    Worker.queue(context.engine, [task.taskUri])
    return True


def disable_dataset_table_copy(
    context: Context,
    source,
    clusterUri: str = None,
    datasetUri: str = None,
    tableUri: str = None,
):
    with context.engine.scoped_session() as session:
        return db.api.RedshiftCluster.disable_copy_table(
            session,
            username=context.username,
            groups=context.groups,
            uri=clusterUri,
            data={'datasetUri': datasetUri, 'tableUri': tableUri},
            check_perm=True,
        )
