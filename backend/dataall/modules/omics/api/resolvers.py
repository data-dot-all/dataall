#
# (c) 2023 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer
# Agreement available at http://aws.amazon.com/agreement or other
# written agreement between Customer and Amazon Web Services, Inc.
#

import logging

from dataall import addons
from dataall.modules.omics.api.enums import OmicsPipelineRole
from dataall.modules.omics.db.api.omics_pipeline import OmicsPipeline
from dataall.api.Objects.Stack import stack_helper
from dataall.api.Objects.Stack.stack_helper import deploy_stack
from dataall.api.context import Context
from dataall.db import models, permissions
from dataall.db.api import Environment, ResourcePolicy, Organization

log = logging.getLogger(__name__)


def create_omics_pipeline(context: Context, source, input=None):
    with context.engine.scoped_session() as session:
        omics_pipeline = OmicsPipeline.create_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input["environmentUri"],
            data=input,
            check_perm=True,
        )

        stack = models.Stack(
            stack="OmicsPipeline",
            accountid=omics_pipeline.AwsAccountId,
            targetUri=omics_pipeline.OmicsPipelineUri,
            region=omics_pipeline.region,
            payload={"account": omics_pipeline.AwsAccountId, "region": omics_pipeline.region},
        )
        session.add(stack)
        session.commit()

        deploy_stack(context, omics_pipeline.OmicsPipelineUri)

    return omics_pipeline

def update_omics_pipeline(context: Context, source, OmicsPipelineUri: str, input: dict = None):
    with context.engine.scoped_session() as session:
        omics_pipeline = OmicsPipeline.update_pipeline(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=OmicsPipelineUri,
            data=input,
            check_perm=True,
        )
        return omics_pipeline


def list_pipelines(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return OmicsPipeline.paginated_user_instances(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=None,
        )


def get_omics_pipeline(context: Context, source, OmicsPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        return OmicsPipeline.get_instance(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=OmicsPipelineUri,
            data=None,
            check_perm=True,
        )


def resolve_user_role(context: Context, source: addons.models.OmicsPipeline):
    if context.username and source.owner == context.username:
        return OmicsPipelineRole.Creator.value
    elif context.groups and source.SamlGroupName in context.groups:
        return OmicsPipelineRole.Admin.value
    return OmicsPipelineRole.NoPermission.value


def resolve_cipipeline_status(context: Context, source: addons.models.OmicsPipeline):
    # call boto3 for codepipeline status
    return source.CiPipelineStatus

def resolve_step_function_status(context: Context, source: addons.models.OmicsPipeline):
    # call boto3 for StepFunctionStatus status
    return source.StepFunctionStatus


def resolve_workflow_status(context: Context, source: addons.models.OmicsPipeline):
    # call boto3 for OmicsWorkflowStatus status
    return source.OmicsWorkflowStatus


def get_omics_pipeline_env(context: Context, source: addons.models.OmicsPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return Environment.find_environment_by_uri(session, source.environmentUri)


def get_omics_pipeline_org(context: Context, source: addons.models.OmicsPipeline, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return Organization.find_organization_by_uri(session, source.environmentUri)


def get_stack(context, source: addons.models.OmicsPipeline, **kwargs):
    return stack_helper.get_stack_with_cfn_resources(
        context=context,
        targetUri=source.OmicsPipelineUri,
        environmentUri=source.environmentUri,
    )


def delete_omics_pipeline(context: Context, source, OmicsPipelineUri: str = None, deleteFromAWS: bool = None):
    with context.engine.scoped_session() as session:
        pipeline = OmicsPipeline.get_pipeline_by_uri(session, OmicsPipelineUri)
        env: models.Environment = Environment.get_environment_by_uri(session, pipeline.environmentUri)
        OmicsPipeline.delete(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=OmicsPipelineUri,
            data={"pipeline": pipeline},
            check_perm=True,
        )

    if deleteFromAWS:
        stack_helper.delete_stack(
            context=context,
            target_uri=OmicsPipelineUri,
            accountid=env.AwsAccountId,
            cdk_role_arn=env.CDKRoleArn,
            region=env.region,
            target_type="OmicsPipeline",
        )

    return True

def update_omics_pipeline_stack(context: Context, source, OmicsPipelineUri: str = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=OmicsPipelineUri,
            permission_name=permissions.UPDATE_OMICS_PIPELINE,
        )
        pipeline = OmicsPipeline.get_pipeline_by_uri(session, OmicsPipelineUri)
    stack_helper.deploy_stack(context=context, targetUri=pipeline.OmicsPipelineUri)
    return True