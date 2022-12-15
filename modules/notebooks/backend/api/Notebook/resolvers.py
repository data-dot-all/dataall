from backend.api.context import Context
from backend.utils.aws.sagemaker import Sagemaker
from backend.utils.aws import stack_helper

from backend.db import (
    core,
    common,
    module
)

from ..constants import SagemakerNotebookRole

def create_notebook(context: Context, source, input: dict = None):
    with context.engine.scoped_session() as session:

        notebook = module.operations.Notebook.create_notebook(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input['environmentUri'],
            data=input,
            check_perm=True,
        )

        common.operations.Stack.create_stack(
            session=session,
            environment_uri=notebook.environmentUri,
            target_type='notebook',
            target_uri=notebook.notebookUri,
            target_label=notebook.label,
        )

    stack_helper.deploy_stack(context=context, targetUri=notebook.notebookUri)

    return notebook


def list_notebooks(context, source, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return module.operations.Notebook.paginated_user_notebooks(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )


def get_notebook(context, source, notebookUri: str = None):
    with context.engine.scoped_session() as session:
        return module.operations.Notebook.get_notebook(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=notebookUri,
            data=None,
            check_perm=True,
        )


def resolve_status(context, source: module.models.SagemakerNotebook, **kwargs):
    if not source:
        return None
    return Sagemaker.get_notebook_instance_status(
        AwsAccountId=source.AWSAccountId,
        region=source.region,
        NotebookInstanceName=source.NotebookInstanceName,
    )


def start_notebook(context, source: module.models.SagemakerNotebook, notebookUri: str = None):
    with context.engine.scoped_session() as session:
        common.operations.ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=notebookUri,
            permission_name=module.permissions.UPDATE_NOTEBOOK,
        )
        notebook = module.operations.Notebook.get_notebook(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=notebookUri,
            data=None,
            check_perm=True,
        )
        Sagemaker.start_instance(
            notebook.AWSAccountId, notebook.region, notebook.NotebookInstanceName
        )
    return 'Starting'


def stop_notebook(context, source: module.models.SagemakerNotebook, notebookUri: str = None):
    with context.engine.scoped_session() as session:
        common.operations.ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=notebookUri,
            permission_name=module.permissions.UPDATE_NOTEBOOK,
        )
        notebook = module.operations.get_notebook(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=notebookUri,
            data=None,
            check_perm=True,
        )
        Sagemaker.stop_instance(
            notebook.AWSAccountId, notebook.region, notebook.NotebookInstanceName
        )
    return 'Stopping'


def get_notebook_presigned_url(
    context, source: module.models.SagemakerNotebook, notebookUri: str = None
):
    with context.engine.scoped_session() as session:
        common.operations.ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=notebookUri,
            permission_name=module.permissions.GET_NOTEBOOK,
        )
        notebook = module.operations.Notebook.get_notebook(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=notebookUri,
            data=None,
            check_perm=True,
        )
        url = Sagemaker.presigned_url(
            notebook.AWSAccountId, notebook.region, notebook.NotebookInstanceName
        )
        return url


def delete_notebook(
    context,
    source: module.models.SagemakerNotebook,
    notebookUri: str = None,
    deleteFromAWS: bool = None,
):
    with context.engine.scoped_session() as session:
        common.operations.ResourcePolicy.check_user_resource_permission(
            session=session,
            resource_uri=notebookUri,
            permission_name=module.permissions.DELETE_NOTEBOOK,
            groups=context.groups,
            username=context.username,
        )
        notebook = module.operations.Notebook.get_notebook_by_uri(session, notebookUri)
        env: core.models.Environment = core.operations.Environment.get_environment_by_uri(
            session, notebook.environmentUri
        )

        core.operations.KeyValueTag.delete_key_value_tags(session, notebook.notebookUri, 'notebook')

        session.delete(notebook)

        common.operations.ResourcePolicy.delete_resource_policy(
            session=session,
            resource_uri=notebook.notebookUri,
            group=notebook.SamlAdminGroupName,
        )

    if deleteFromAWS:
        stack_helper.delete_stack(
            context=context,
            target_uri=notebookUri,
            accountid=env.AwsAccountId,
            cdk_role_arn=env.CDKRoleArn,
            region=env.region,
            target_type='notebook',
        )

    return True


def resolve_environment(context, source, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return session.query(core.models.Environment).get(source.environmentUri)


def resolve_organization(context, source, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        env: core.models.Environment = session.query(core.models.Environment).get(
            source.environmentUri
        )
        return session.query(core.models.Organization).get(env.organizationUri)


def resolve_user_role(context: Context, source: module.models.SagemakerNotebook):
    if not source:
        return None
    if source.owner == context.username:
        return SagemakerNotebookRole.Creator.value
    elif context.groups and source.SamlAdminGroupName in context.groups:
        return SagemakerNotebookRole.Admin.value
    return SagemakerNotebookRole.NoPermission.value


def resolve_stack(context: Context, source: module.models.SagemakerNotebook, **kwargs):
    if not source:
        return None
    return stack_helper.get_stack_with_cfn_resources(
        context=context,
        targetUri=source.notebookUri,
        environmentUri=source.environmentUri,
    )
