import json
import logging

from dataall.base.aws.sts import SessionHelper
from dataall.base.context import get_context
from dataall.base.db import exceptions
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.services.group_policy_service import GroupPolicyService
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.stacks.db.keyvaluetag_repositories import KeyValueTagRepository
from dataall.core.stacks.db.stack_repositories import StackRepository
from dataall.core.stacks.services.stack_service import StackService
from dataall.core.tasks.db.task_models import Task
from dataall.core.tasks.service_handlers import Worker
from dataall.modules.datapipelines.db.datapipelines_models import DataPipeline, DataPipelineEnvironment
from dataall.modules.datapipelines.db.datapipelines_repositories import DatapipelinesRepository
from dataall.modules.datapipelines.services.datapipelines_permissions import (
    DELETE_PIPELINE,
    CREDENTIALS_PIPELINE,
    MANAGE_PIPELINES,
    CREATE_PIPELINE,
    PIPELINE_ALL,
    GET_PIPELINE,
    UPDATE_PIPELINE,
)

logger = logging.getLogger(__name__)


def _session():
    return get_context().db_engine.scoped_session()


class DataPipelineService:
    @staticmethod
    def _get_pipeline_uri_from_env_uri(session, envPipelineUri):
        return DatapipelinesRepository.get_pipeline_environment_by_uri(session, envPipelineUri).pipelineUri

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_PIPELINES)
    @ResourcePolicyService.has_resource_permission(CREATE_PIPELINE)
    @GroupPolicyService.has_group_permission(CREATE_PIPELINE)
    def create_pipeline(
        uri: str,
        admin_group: str,
        data: dict = None,
    ) -> DataPipeline:
        with _session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)
            enabled = EnvironmentService.get_boolean_env_param(session, environment, 'pipelinesEnabled')

            if not enabled:
                raise exceptions.UnauthorizedOperation(
                    action=CREATE_PIPELINE,
                    message=f'Pipelines feature is disabled for the environment {environment.label}',
                )

            pipeline = DatapipelinesRepository.create_pipeline(
                session=session,
                username=get_context().username,
                admin_group=admin_group,
                uri=environment.environmentUri,
                data=data,
            )

            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=admin_group,
                permissions=PIPELINE_ALL,
                resource_uri=pipeline.DataPipelineUri,
                resource_type=DataPipeline.__name__,
            )

            if environment.SamlGroupName != pipeline.SamlGroupName:
                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    group=environment.SamlGroupName,
                    permissions=PIPELINE_ALL,
                    resource_uri=pipeline.DataPipelineUri,
                    resource_type=DataPipeline.__name__,
                )

            if data['devStrategy'] == 'cdk-trunk':
                StackRepository.create_stack(
                    session=session,
                    environment_uri=pipeline.environmentUri,
                    target_type='cdkpipeline',
                    target_uri=pipeline.DataPipelineUri,
                    payload={'account': pipeline.AwsAccountId, 'region': pipeline.region},
                )
            else:
                StackRepository.create_stack(
                    session=session,
                    environment_uri=pipeline.environmentUri,
                    target_type='pipeline',
                    target_uri=pipeline.DataPipelineUri,
                    payload={'account': pipeline.AwsAccountId, 'region': pipeline.region},
                )

            StackService.deploy_stack(pipeline.DataPipelineUri)
            return pipeline

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_PIPELINES)
    @ResourcePolicyService.has_resource_permission(CREATE_PIPELINE)
    @GroupPolicyService.has_group_permission(CREATE_PIPELINE)
    def create_pipeline_environment(
        uri: str,
        admin_group: str,
        data: dict = None,
    ) -> DataPipelineEnvironment:
        with _session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, data['environmentUri'])
            enabled = EnvironmentService.get_boolean_env_param(session, environment, 'pipelinesEnabled')

            if not enabled:
                raise exceptions.UnauthorizedOperation(
                    action=CREATE_PIPELINE,
                    message=f'Pipelines feature is disabled for the environment {environment.label}',
                )

            pipeline = DatapipelinesRepository.get_pipeline_by_uri(session, data['pipelineUri'])

            pipeline_env: DataPipelineEnvironment = DataPipelineEnvironment(
                owner=get_context().username,
                label=f'{pipeline.label}-{environment.label}',
                environmentUri=environment.environmentUri,
                environmentLabel=environment.label,
                pipelineUri=pipeline.DataPipelineUri,
                pipelineLabel=pipeline.label,
                envPipelineUri=f'{pipeline.DataPipelineUri}{environment.environmentUri}{data["stage"]}',
                AwsAccountId=environment.AwsAccountId,
                region=environment.region,
                stage=data['stage'],
                order=data['order'],
                samlGroupName=data['samlGroupName'],
            )

            session.add(pipeline_env)
            session.commit()

            return pipeline_env

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_PIPELINES)
    @ResourcePolicyService.has_resource_permission(UPDATE_PIPELINE)
    def update_pipeline(uri, data=None) -> DataPipeline:
        with _session() as session:
            pipeline: DataPipeline = DatapipelinesRepository.get_pipeline_by_uri(session, uri)
            if data:
                if isinstance(data, dict):
                    for k in data.keys():
                        setattr(pipeline, k, data.get(k))
            if pipeline.template == '':
                StackService.deploy_stack(pipeline.DataPipelineUri)
            return pipeline

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_PIPELINES)
    @ResourcePolicyService.has_resource_permission(UPDATE_PIPELINE)
    def update_pipeline_environment(uri, data=None) -> DataPipelineEnvironment:
        with _session() as session:
            pipeline_env = DatapipelinesRepository.get_pipeline_environment(
                session=session, pipelineUri=uri, environmentUri=data['environmentUri'], stage=data['stage']
            )

            if data:
                if isinstance(data, dict):
                    for k in data.keys():
                        print(f'KEY: {k}, VALUE: {data.get(k)}')
                        setattr(pipeline_env, k, data.get(k))
            return pipeline_env

    @staticmethod
    def list_pipelines(*, filter: dict) -> dict:
        with _session() as session:
            return DatapipelinesRepository.paginated_user_pipelines(
                session=session,
                username=get_context().username,
                groups=get_context().groups,
                data=filter,
            )

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_PIPELINE)
    def get_pipeline(
        uri: str,
    ) -> DataPipeline:
        context = get_context()
        with _session() as session:
            return DatapipelinesRepository.get_pipeline_by_uri(session, uri)

    @staticmethod
    def list_pipeline_environments(*, uri, filter: dict) -> dict:
        with _session() as session:
            return DatapipelinesRepository.paginated_pipeline_environments(session=session, uri=uri, data=filter)

    @staticmethod
    def get_clone_url_http(uri: str):
        with _session() as session:
            pipeline = DatapipelinesRepository.get_pipeline_by_uri(session, uri)
            env = EnvironmentService.get_environment_by_uri(session, pipeline.environmentUri)
            return f'codecommit::{env.region}://{pipeline.repo}'

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_PIPELINES)
    @ResourcePolicyService.has_resource_permission(DELETE_PIPELINE)
    def delete_pipeline(uri: str, deleteFromAWS: bool):
        with _session() as session:
            pipeline = DatapipelinesRepository.get_pipeline_by_uri(session, uri)
            env = EnvironmentService.get_environment_by_uri(session, pipeline.environmentUri)

            if deleteFromAWS:
                DataPipelineService._delete_repository(
                    target_uri=pipeline.DataPipelineUri,
                    accountid=env.AwsAccountId,
                    cdk_role_arn=env.CDKRoleArn,
                    region=env.region,
                    repo_name=pipeline.repo,
                )
                StackService.delete_stack(
                    target_uri=pipeline.DataPipelineUri,
                    accountid=env.AwsAccountId,
                    cdk_role_arn=env.CDKRoleArn,
                    region=env.region,
                )

            DatapipelinesRepository.delete_pipeline_environments(session, uri)
            KeyValueTagRepository.delete_key_value_tags(session, pipeline.DataPipelineUri, 'pipeline')

            session.delete(pipeline)

            ResourcePolicyService.delete_resource_policy(
                session=session,
                resource_uri=pipeline.DataPipelineUri,
                group=pipeline.SamlGroupName,
            )
            return True

    @staticmethod
    def _delete_repository(target_uri, accountid, cdk_role_arn, region, repo_name):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            task = Task(
                targetUri=target_uri,
                action='repo.datapipeline.delete',
                payload={
                    'accountid': accountid,
                    'region': region,
                    'cdk_role_arn': cdk_role_arn,
                    'repo_name': repo_name,
                },
            )
            session.add(task)
        Worker.queue(context.db_engine, [task.taskUri])
        return True

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_PIPELINES)
    @ResourcePolicyService.has_resource_permission(
        UPDATE_PIPELINE, param_name='envPipelineUri', parent_resource=_get_pipeline_uri_from_env_uri
    )
    def delete_pipeline_environment(envPipelineUri: str):
        with _session() as session:
            DatapipelinesRepository.delete_pipeline_environment(session=session, envPipelineUri=envPipelineUri)
            return True

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_PIPELINES)
    @ResourcePolicyService.has_resource_permission(CREDENTIALS_PIPELINE)
    def get_credentials(uri):
        with _session() as session:
            pipeline = DatapipelinesRepository.get_pipeline_by_uri(session, uri)
            env = EnvironmentService.get_environment_by_uri(session, pipeline.environmentUri)

            env_role_arn = env.EnvironmentDefaultIAMRoleArn
            aws_account_id = pipeline.AwsAccountId

            return DataPipelineService._get_credentials_from_aws(
                env_role_arn=env_role_arn, aws_account_id=aws_account_id, region=pipeline.region
            )

    @staticmethod
    def _get_credentials_from_aws(env_role_arn, aws_account_id, region):
        aws_session = SessionHelper.remote_session(aws_account_id, region)
        env_session = SessionHelper.get_session(aws_session, role_arn=env_role_arn)
        c = env_session.get_credentials()
        body = json.dumps(
            {
                'AWS_ACCESS_KEY_ID': c.access_key,
                'AWS_SECRET_ACCESS_KEY': c.secret_key,
                'AWS_SESSION_TOKEN': c.token,
            }
        )
        return body
