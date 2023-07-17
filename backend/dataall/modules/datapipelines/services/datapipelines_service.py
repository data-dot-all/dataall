import json
import logging

from dataall.aws.handlers.sts import SessionHelper
from dataall.core.activity.db.activity_models import Activity
from dataall.core.environment.env_permission_checker import has_group_permission
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.db.resource_policy import ResourcePolicy
from dataall.core.permissions.permission_checker import has_resource_permission, has_tenant_permission
from dataall.core.stacks.db.keyvaluetag import KeyValueTag
from dataall.db import exceptions
from dataall.modules.datapipelines.aws.codecommit_datapipeline_client import DatapipelineCodecommitClient
from dataall.modules.datapipelines.aws.codepipeline_datapipeline_client import CodepipelineDatapipelineClient
from dataall.modules.datapipelines.aws.glue_datapipeline_client import GlueDatapipelineClient
from dataall.modules.datapipelines.db.models import DataPipeline, DataPipelineEnvironment
from dataall.modules.datapipelines.db.repositories import DatapipelinesRepository
from dataall.modules.datapipelines.services.datapipelines_permissions import DELETE_PIPELINE, \
    CREDENTIALS_PIPELINE, MANAGE_PIPELINES, CREATE_PIPELINE, PIPELINE_ALL, GET_PIPELINE, UPDATE_PIPELINE
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from dataall.base.utils import slugify

logger = logging.getLogger(__name__)


class DataPipelineService:
    @staticmethod
    @has_tenant_permission(MANAGE_PIPELINES)
    @has_resource_permission(CREATE_PIPELINE)
    @has_group_permission(CREATE_PIPELINE)
    def create_pipeline(
        session,
        admin_group,
        username: str,
        uri: str,
        data: dict = None,
    ) -> DataPipeline:

        environment = EnvironmentService.get_environment_by_uri(session, uri)
        enabled = EnvironmentService.get_boolean_env_param(session, environment, "pipelinesEnabled")

        if not enabled:
            raise exceptions.UnauthorizedOperation(
                action=CREATE_PIPELINE,
                message=f'Pipelines feature is disabled for the environment {environment.label}',
            )

        pipeline: DataPipeline = DataPipeline(
            owner=username,
            environmentUri=environment.environmentUri,
            SamlGroupName=admin_group,
            label=data['label'],
            description=data.get('description', 'No description provided'),
            tags=data.get('tags', []),
            AwsAccountId=environment.AwsAccountId,
            region=environment.region,
            repo=slugify(data['label']),
            devStrategy=data['devStrategy'],
            template="",
        )

        session.add(pipeline)
        session.commit()

        aws_compliant_name = NamingConventionService(
            target_uri=pipeline.DataPipelineUri,
            target_label=pipeline.label,
            pattern=NamingConventionPattern.DEFAULT,
            resource_prefix=environment.resourcePrefix,
        ).build_compliant_name()

        pipeline.repo = aws_compliant_name
        pipeline.name = aws_compliant_name

        activity = Activity(
            action='PIPELINE:CREATE',
            label='PIPELINE:CREATE',
            owner=username,
            summary=f'{username} created dashboard {pipeline.label} in {environment.label}',
            targetUri=pipeline.DataPipelineUri,
            targetType='pipeline',
        )
        session.add(activity)

        ResourcePolicy.attach_resource_policy(
            session=session,
            group=data['SamlGroupName'],
            permissions=PIPELINE_ALL,
            resource_uri=pipeline.DataPipelineUri,
            resource_type=DataPipeline.__name__,
        )

        if environment.SamlGroupName != pipeline.SamlGroupName:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=environment.SamlGroupName,
                permissions=PIPELINE_ALL,
                resource_uri=pipeline.DataPipelineUri,
                resource_type=DataPipeline.__name__,
            )

        return pipeline

    @staticmethod
    @has_group_permission(CREATE_PIPELINE)
    def create_pipeline_environment(
        session,
        admin_group,
        uri,
        username: str,
        data: dict = None,
    ) -> DataPipelineEnvironment:

        environment = EnvironmentService.get_environment_by_uri(session, data['environmentUri'])
        enabled = EnvironmentService.get_boolean_env_param(session, environment, "pipelinesEnabled")

        if not enabled:
            raise exceptions.UnauthorizedOperation(
                action=CREATE_PIPELINE,
                message=f'Pipelines feature is disabled for the environment {environment.label}',
            )

        pipeline = DatapipelinesRepository.get_pipeline_by_uri(session, data['pipelineUri'])

        pipeline_env: DataPipelineEnvironment = DataPipelineEnvironment(
            owner=username,
            label=f"{pipeline.label}-{environment.label}",
            environmentUri=environment.environmentUri,
            environmentLabel=environment.label,
            pipelineUri=pipeline.DataPipelineUri,
            pipelineLabel=pipeline.label,
            envPipelineUri=f"{pipeline.DataPipelineUri}{environment.environmentUri}{data['stage']}",
            AwsAccountId=environment.AwsAccountId,
            region=environment.region,
            stage=data['stage'],
            order=data['order'],
            samlGroupName=data['samlGroupName']
        )

        session.add(pipeline_env)
        session.commit()

        return pipeline_env

    @staticmethod
    def validate_group_membership(
        session, environment_uri, pipeline_group, username, groups
    ):
        if pipeline_group and pipeline_group not in groups:
            raise exceptions.UnauthorizedOperation(
                action=CREATE_PIPELINE,
                message=f'User: {username} is not a member of the team {pipeline_group}',
            )
        if pipeline_group not in EnvironmentService.list_environment_groups(
            session=session,
            uri=environment_uri,
        ):
            raise exceptions.UnauthorizedOperation(
                action=CREATE_PIPELINE,
                message=f'Team: {pipeline_group} is not a member of the environment {environment_uri}',
            )

    @staticmethod
    @has_tenant_permission(MANAGE_PIPELINES)
    @has_resource_permission(GET_PIPELINE)
    def get_pipeline(
        session,
        uri: str,
    ) -> DataPipeline:
        return DatapipelinesRepository.get_pipeline_by_uri(session, uri)

    @staticmethod
    @has_tenant_permission(MANAGE_PIPELINES)
    @has_resource_permission(UPDATE_PIPELINE)
    def update_pipeline(
        session, uri, data=None
    ) -> DataPipeline:
        pipeline: DataPipeline = DatapipelinesRepository.get_pipeline_by_uri(session, uri)
        if data:
            if isinstance(data, dict):
                for k in data.keys():
                    setattr(pipeline, k, data.get(k))
        return pipeline

    @staticmethod
    def delete(session, username, groups, uri, data=None, check_perm=None) -> bool:
        pipeline = DatapipelinesRepository.get_pipeline_by_uri(session, uri)
        ResourcePolicy.delete_resource_policy(
            session=session, resource_uri=uri, group=pipeline.SamlGroupName
        )
        session.delete(pipeline)
        session.commit()
        return True

    @staticmethod
    @has_tenant_permission(MANAGE_PIPELINES)
    @has_resource_permission(GET_PIPELINE)
    def get_pipeline_environment(
        session,
        uri: str,
    ) -> DataPipeline:
        return DatapipelinesRepository.get_pipeline_environment_by_uri(session, uri)

    @staticmethod
    @has_tenant_permission(MANAGE_PIPELINES)
    @has_resource_permission(UPDATE_PIPELINE)
    def update_pipeline_environment(
        session, uri, data=None
    ) -> DataPipelineEnvironment:
        pipeline_env = DatapipelinesRepository.get_pipeline_environment(
            session=session,
            pipelineUri=data['pipelineUri'],
            environmentUri=data['environmentUri'],
            stage=data['stage']
        )

        if data:
            if isinstance(data, dict):
                for k in data.keys():
                    print(f"KEY: {k}, VALUE: {data.get(k)}")
                    setattr(pipeline_env, k, data.get(k))
        return pipeline_env

    @staticmethod
    @has_resource_permission(DELETE_PIPELINE)
    def delete_pipeline(session, uri, pipeline):

        DatapipelinesRepository.delete_pipeline_environments(session, uri)

        KeyValueTag.delete_key_value_tags(session, pipeline.DataPipelineUri, 'pipeline')

        session.delete(pipeline)

        ResourcePolicy.delete_resource_policy(
            session=session,
            resource_uri=pipeline.DataPipelineUri,
            group=pipeline.SamlGroupName,
        )

    @staticmethod
    def _get_creds_from_aws(pipeline, env_role_arn):
        aws_account_id = pipeline.AwsAccountId
        aws_session = SessionHelper.remote_session(aws_account_id)
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

    @staticmethod
    @has_resource_permission(CREDENTIALS_PIPELINE)
    def get_credentials(session, uri):
        pipeline = DatapipelinesRepository.get_pipeline_by_uri(session, uri)
        env = EnvironmentService.get_environment_by_uri(session, pipeline.environmentUri)

        env_role_arn = env.EnvironmentDefaultIAMRoleArn

        return DataPipelineService._get_creds_from_aws(pipeline, env_role_arn)

    @staticmethod
    @has_tenant_permission(MANAGE_PIPELINES)
    @has_resource_permission(GET_PIPELINE)
    def cat(session, input):
        (pipeline, env) = DatapipelinesRepository.get_pipeline_and_environment_by_uri(
            session=session,
            uri=input.get('DataPipelineUri')
        )

        return DatapipelineCodecommitClient(env.AwsAccountId, env.region).get_file_content(
            repository=pipeline.repo,
            commit_specifier=input.get('branch', 'master'),
            file_path=input.get('absolutePath', 'README.md')
        )

    @staticmethod
    @has_tenant_permission(MANAGE_PIPELINES)
    @has_resource_permission(GET_PIPELINE)
    def ls(session, input):
        (pipeline, env) = DatapipelinesRepository.get_pipeline_and_environment_by_uri(
            session=session,
            uri=input.get('DataPipelineUri')
        )

        return DatapipelineCodecommitClient(env.AwsAccountId, env.region).get_folder_content(
            repository=pipeline.repo,
            commit_specifier=input.get('branch', 'master'),
            folder_path=input.get('folderPath', '/')
        )

    @staticmethod
    @has_tenant_permission(MANAGE_PIPELINES)
    @has_resource_permission(GET_PIPELINE)
    def list_branches(session, datapipeline_uri):
        (pipeline, env) = DatapipelinesRepository.get_pipeline_and_environment_by_uri(
            session=session,
            uri=datapipeline_uri
        )

        return DatapipelineCodecommitClient(env.AwsAccountId, env.region).list_branches(
            repository=pipeline.repo
        )

    @staticmethod
    def get_job_runs(session, datapipeline_uri):
        data_pipeline: DataPipeline = DatapipelinesRepository.get_pipeline_by_uri(
            session=session,
            uri=datapipeline_uri
        )

        return GlueDatapipelineClient(
            aws_account_id=data_pipeline.AwsAccountId,
            region=data_pipeline.region
        ).get_job_runs(datapipeline_job_name=data_pipeline.name)

    @staticmethod
    def get_pipeline_execution(session, datapipeline_uri):
        stack = DatapipelinesRepository.get_pipeline_stack_by_uri(session, datapipeline_uri)
        datapipeline: DataPipeline = DatapipelinesRepository.get_pipeline_by_uri(session, datapipeline_uri)
        outputs = stack.outputs
        codepipeline_name = outputs['PipelineNameOutput']

        return CodepipelineDatapipelineClient(
            aws_account_id=datapipeline.AwsAccountId,
            region=datapipeline.region
        ).get_pipeline_execution_summaries(codepipeline_name=codepipeline_name)
