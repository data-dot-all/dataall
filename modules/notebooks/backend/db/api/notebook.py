import logging

from sqlalchemy import or_
from sqlalchemy.orm import Query


from backend.db.api import (
    has_tenant_perm,
    has_resource_perm,
    ResourcePolicy,
)
from backend.db import (
    exceptions,
    paginate
)

from backend.db.core import permissions
from backend.db.core.api import Environment
from backend.db.core.models import EnvironmentGroup

from backend.db.module.models import SagemakerNotebook

from backend.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from  backend.utils.utils.slugify import slugify

logger = logging.getLogger(__name__)


class Notebook:
    @staticmethod
    @has_tenant_perm(permissions.MANAGE_NOTEBOOKS)
    @has_resource_perm(permissions.CREATE_NOTEBOOK)
    def create_notebook(
        session, username, groups, uri, data=None, check_perm=None
    ) -> SagemakerNotebook:

        Notebook.validate_params(data)

        Environment.check_group_environment_permission(
            session=session,
            username=username,
            groups=groups,
            uri=uri,
            group=data['SamlAdminGroupName'],
            permission_name=permissions.CREATE_NOTEBOOK,
        )

        env = Environment.get_environment_by_uri(session, uri)

        if not env.notebooksEnabled:
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_NOTEBOOK,
                message=f'Notebooks feature is disabled for the environment {env.label}',
            )

        env_group: EnvironmentGroup = data.get(
            'environment',
            Environment.get_environment_group(
                session,
                group_uri=data['SamlAdminGroupName'],
                environment_uri=env.environmentUri,
            ),
        )

        notebook = SagemakerNotebook(
            label=data.get('label', 'Untitled'),
            environmentUri=env.environmentUri,
            description=data.get('description', 'No description provided'),
            NotebookInstanceName=slugify(data.get('label'), separator=''),
            NotebookInstanceStatus='NotStarted',
            AWSAccountId=env.AwsAccountId,
            region=env.region,
            RoleArn=env_group.environmentIAMRoleArn,
            owner=username,
            SamlAdminGroupName=data.get('SamlAdminGroupName', env.SamlGroupName),
            tags=data.get('tags', []),
            VpcId=data.get('VpcId'),
            SubnetId=data.get('SubnetId'),
            VolumeSizeInGB=data.get('VolumeSizeInGB', 32),
            InstanceType=data.get('InstanceType', 'ml.t3.medium'),
        )
        session.add(notebook)
        session.commit()

        notebook.NotebookInstanceName = NamingConventionService(
            target_uri=notebook.notebookUri,
            target_label=notebook.label,
            pattern=NamingConventionPattern.DEFAULT,
            resource_prefix=env.resourcePrefix,
        ).build_compliant_name()

        ResourcePolicy.attach_resource_policy(
            session=session,
            group=data['SamlAdminGroupName'],
            permissions=permissions.NOTEBOOK_ALL,
            resource_uri=notebook.notebookUri,
            resource_type=SagemakerNotebook.__name__,
        )

        if env.SamlGroupName != notebook.SamlAdminGroupName:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=env.SamlGroupName,
                permissions=permissions.NOTEBOOK_ALL,
                resource_uri=notebook.notebookUri,
                resource_type=SagemakerNotebook.__name__,
            )

        return notebook

    @staticmethod
    def validate_params(data):
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('environmentUri'):
            raise exceptions.RequiredParameter('environmentUri')
        if not data.get('label'):
            raise exceptions.RequiredParameter('name')

    @staticmethod
    def query_user_notebooks(session, username, groups, filter) -> Query:
        query = session.query(SagemakerNotebook).filter(
            or_(
                SagemakerNotebook.owner == username,
                SagemakerNotebook.SamlAdminGroupName.in_(groups),
            )
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    SagemakerNotebook.description.ilike(
                        filter.get('term') + '%%'
                    ),
                    SagemakerNotebook.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query

    @staticmethod
    def paginated_user_notebooks(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=Notebook.query_user_notebooks(session, username, groups, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    @has_resource_perm(permissions.GET_NOTEBOOK)
    def get_notebook(session, username, groups, uri, data=None, check_perm=True):
        return Notebook.get_notebook_by_uri(session, uri)

    @staticmethod
    def get_notebook_by_uri(session, uri) -> SagemakerNotebook:
        if not uri:
            raise exceptions.RequiredParameter('URI')
        notebook = session.query(SagemakerNotebook).get(uri)
        if not notebook:
            raise exceptions.ObjectNotFound('SagemakerNotebook', uri)
        return notebook
