import logging

from sqlalchemy import or_
from sqlalchemy.orm import Query

from .. import exceptions, permissions, paginate, models
from . import (
    has_tenant_perm,
    has_resource_perm,
    ResourcePolicy,
    Environment,
)

logger = logging.getLogger(__name__)


class SgmStudioNotebook:
    @staticmethod
    @has_tenant_perm(permissions.MANAGE_NOTEBOOKS)
    @has_resource_perm(permissions.CREATE_SGMSTUDIO_NOTEBOOK)
    def create_notebook(session, username, groups, uri, data=None, check_perm=None):

        SgmStudioNotebook.validate_params(data)

        Environment.check_group_environment_permission(
            session=session,
            username=username,
            groups=groups,
            uri=uri,
            group=data["SamlAdminGroupName"],
            permission_name=permissions.CREATE_SGMSTUDIO_NOTEBOOK,
        )

        env: models.Environment = data.get("environment", Environment.get_environment_by_uri(session, uri))

        sm_user_profile = models.SagemakerStudioUserProfile(
            label=data.get("label", f"UserProfile-{username}"),
            environmentUri=uri,
            description=data.get("description", "No description provided"),
            sagemakerStudioUserProfileName=data.get("label", f"up-{username}"),
            sagemakerStudioUserProfileStatus="PENDING",
            sagemakerStudioDomainID=data["domain_id"],
            AWSAccountId=env.AwsAccountId,
            region=env.region,
            RoleArn=env.EnvironmentDefaultIAMRoleArn,
            owner=username,
            SamlAdminGroupName=data["SamlAdminGroupName"],
            tags=data.get("tags", []),
        )
        session.add(sm_user_profile)
        session.commit()

        ResourcePolicy.attach_resource_policy(
            session=session,
            group=data["SamlAdminGroupName"],
            permissions=permissions.SGMSTUDIO_NOTEBOOK_ALL,
            resource_uri=sm_user_profile.sagemakerStudioUserProfileUri,
            resource_type=models.SagemakerStudioUserProfile.__name__,
        )

        if env.SamlGroupName != sm_user_profile.SamlAdminGroupName:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=env.SamlGroupName,
                permissions=permissions.SGMSTUDIO_NOTEBOOK_ALL,
                resource_uri=sm_user_profile.sagemakerStudioUserProfileUri,
                resource_type=models.SagemakerStudioUserProfile.__name__,
            )

        return sm_user_profile

    @staticmethod
    def validate_params(data):
        if not data:
            raise exceptions.RequiredParameter("data")
        if not data.get("environmentUri"):
            raise exceptions.RequiredParameter("environmentUri")
        if not data.get("label"):
            raise exceptions.RequiredParameter("name")

    @staticmethod
    def validate_group_membership(session, environment_uri, notebook_group, username, groups):
        if notebook_group and notebook_group not in groups:
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_SGMSTUDIO_NOTEBOOK,
                message=f"User: {username} is not a member of the team {notebook_group}",
            )
        if notebook_group not in Environment.list_environment_groups(
            session=session,
            username=username,
            groups=groups,
            uri=environment_uri,
            data=None,
            check_perm=True,
        ):
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_SGMSTUDIO_NOTEBOOK,
                message=f"Team: {notebook_group} is not a member of the environment {environment_uri}",
            )

    @staticmethod
    def query_user_notebooks(session, username, groups, filter) -> Query:
        query = session.query(models.SagemakerStudioUserProfile).filter(
            or_(
                models.SagemakerStudioUserProfile.owner == username,
                models.SagemakerStudioUserProfile.SamlAdminGroupName.in_(groups),
            )
        )
        if filter and filter.get("term"):
            query = query.filter(
                or_(
                    models.SagemakerStudioUserProfile.description.ilike(filter.get("term") + "%%"),
                    models.SagemakerStudioUserProfile.label.ilike(filter.get("term") + "%%"),
                )
            )
        return query

    @staticmethod
    def paginated_user_notebooks(session, username, groups, uri, data=None, check_perm=None) -> dict:
        return paginate(
            query=SgmStudioNotebook.query_user_notebooks(session, username, groups, data),
            page=data.get("page", 1),
            page_size=data.get("pageSize", 10),
        ).to_dict()

    @staticmethod
    @has_resource_perm(permissions.GET_SGMSTUDIO_NOTEBOOK)
    def get_notebook(session, username, groups, uri, data=None, check_perm=True):
        return SgmStudioNotebook.get_notebook_by_uri(session, uri)

    @staticmethod
    def get_notebook_by_uri(session, uri) -> models.SagemakerStudioUserProfile:
        if not uri:
            raise exceptions.RequiredParameter("URI")
        notebook = session.query(models.SagemakerStudioUserProfile).get(uri)
        if not notebook:
            raise exceptions.ObjectNotFound("SagemakerStudioUserProfile", uri)
        return notebook
