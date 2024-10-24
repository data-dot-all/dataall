"""
A service layer for Omics pipelines
Central part for working with Omics workflow runs
"""

import dataclasses
import logging
from dataclasses import dataclass, field
from typing import List, Dict


from dataall.base.context import get_context
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.permissions.services.group_policy_service import GroupPolicyService
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.base.db import exceptions
import json

from dataall.modules.omics.db.omics_repository import OmicsRepository
from dataall.modules.omics.aws.omics_client import OmicsClient
from dataall.modules.omics.db.omics_models import OmicsRun
from dataall.modules.omics.services.omics_permissions import (
    MANAGE_OMICS_RUNS,
    CREATE_OMICS_RUN,
    OMICS_RUN_ALL,
    DELETE_OMICS_RUN,
)

logger = logging.getLogger(__name__)


class OmicsService:
    """
    Encapsulate the logic of interactions with Omics.
    """

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_OMICS_RUNS)
    @ResourcePolicyService.has_resource_permission(CREATE_OMICS_RUN)
    @GroupPolicyService.has_group_permission(CREATE_OMICS_RUN)
    def create_omics_run(*, uri: str, admin_group: str, data: dict) -> OmicsRun:
        """
        Creates an omics_run and attach policies to it
        Throws an exception if omics_run are not enabled for the environment
        """

        with _session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)
            dataset = DatasetRepository.get_dataset_by_uri(session, data['destination'])
            enabled = EnvironmentService.get_boolean_env_param(session, environment, 'omicsEnabled')
            workflow = OmicsRepository(session=session).get_workflow(workflowUri=data['workflowUri'])
            group = EnvironmentService.get_environment_group(session, admin_group, environment.environmentUri)

            if not enabled and enabled.lower() != 'true':
                raise exceptions.UnauthorizedOperation(
                    action=CREATE_OMICS_RUN,
                    message=f'OMICS_RUN feature is disabled for the environment {environment.label}',
                )

            omics_run = OmicsRun(
                owner=get_context().username,
                organizationUri=environment.organizationUri,
                environmentUri=environment.environmentUri,
                SamlAdminGroupName=admin_group,
                workflowUri=data['workflowUri'],
                parameterTemplate=data['parameterTemplate'],
                label=data['label'],
                outputUri=f's3://{dataset.S3BucketName}',
                outputDatasetUri=dataset.datasetUri,
            )

            response = OmicsClient(awsAccountId=environment.AwsAccountId, region=environment.region).run_omics_workflow(
                omics_workflow=workflow, omics_run=omics_run, role_arn=group.environmentIAMRoleArn
            )

            omics_run.runUri = response['id']
            OmicsRepository(session).save_omics_run(omics_run)

            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=omics_run.SamlAdminGroupName,
                permissions=OMICS_RUN_ALL,
                resource_uri=omics_run.runUri,
                resource_type=OmicsRun.__name__,
            )
            OmicsRepository(session).save_omics_run(omics_run)

            return omics_run

    @staticmethod
    def _get_omics_run(uri: str):
        with _session() as session:
            return OmicsRepository(session).get_omics_run(uri)

    @staticmethod
    def get_omics_run_details_from_aws(uri: str):
        with _session() as session:
            omics_run = OmicsRepository(session).get_omics_run(runUri=uri)
            environment = EnvironmentService.get_environment_by_uri(session=session, uri=omics_run.environmentUri)
            return OmicsClient(awsAccountId=environment.AwsAccountId, region=environment.region).get_omics_run(uri)

    @staticmethod
    def get_omics_workflow(uri: str) -> dict:
        """Get Omics workflow."""
        with _session() as session:
            workflow = OmicsRepository(session).get_workflow(workflowUri=uri)
            environment = EnvironmentService.get_environment_by_uri(session=session, uri=workflow.environmentUri)
            response = OmicsClient(awsAccountId=environment.AwsAccountId, region=environment.region).get_omics_workflow(
                workflow
            )
            parameterTemplateJson = json.dumps(response['parameterTemplate'])
            response['parameterTemplate'] = parameterTemplateJson
            response['workflowUri'] = uri
        return response

    @staticmethod
    def list_user_omics_runs(filter: dict) -> dict:
        """List existed user Omics runs. Filters only required omics_runs by the filter param"""
        with _session() as session:
            return OmicsRepository(session).paginated_user_runs(
                username=get_context().username, groups=get_context().groups, filter=filter
            )

    @staticmethod
    def list_omics_workflows(filter: dict) -> dict:
        """List Omics workflows."""
        with _session() as session:
            return OmicsRepository(session).paginated_omics_workflows(filter=filter)

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_OMICS_RUNS)
    def delete_omics_runs(uris: List[str], delete_from_aws: bool) -> bool:
        """Deletes Omics runs from the database and if delete_from_aws is True from AWS as well"""
        for uri in uris:
            OmicsService.delete_omics_run(uri=uri, delete_from_aws=delete_from_aws)
        return True

    @staticmethod
    @ResourcePolicyService.has_resource_permission(DELETE_OMICS_RUN)
    def delete_omics_run(*, uri: str, delete_from_aws: bool):
        """Deletes Omics run from the database and if delete_from_aws is True from AWS as well"""
        with _session() as session:
            omics_run = OmicsService._get_omics_run(uri)
            environment = EnvironmentService.get_environment_by_uri(session=session, uri=omics_run.environmentUri)
            if not omics_run:
                raise exceptions.ObjectNotFound('OmicsRun', uri)
            if delete_from_aws:
                OmicsClient(awsAccountId=environment.AwsAccountId, region=environment.region).delete_omics_run(
                    uri=omics_run.runUri
                )
            session.delete(omics_run)

            ResourcePolicyService.delete_resource_policy(
                session=session,
                resource_uri=omics_run.runUri,
                group=omics_run.SamlAdminGroupName,
            )


def _session():
    return get_context().db_engine.scoped_session()
