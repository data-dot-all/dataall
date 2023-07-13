from dataall.core.environment.db.models import EnvironmentGroup
from dataall.core.permissions.db.resource_policy import ResourcePolicy
from dataall.db.exceptions import UnauthorizedOperation


class GroupPolicy:
    """Checks permission of environment group"""
    @staticmethod
    def check_group_environment_permission(
            session, username, groups, uri, group, permission_name
    ):
        GroupPolicy.check_group_environment_membership(
            session=session,
            username=username,
            user_groups=groups,
            group=group,
            environment_uri=uri,
            permission_name=permission_name,
        )

        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=username,
            groups=[group],
            resource_uri=uri,
            permission_name=permission_name,
        )

    @staticmethod
    def check_group_environment_membership(
            session, environment_uri, group, username, user_groups, permission_name
    ):
        if group and group not in user_groups:
            raise UnauthorizedOperation(
                action=permission_name,
                message=f'User: {username} is not a member of the team {group}',
            )

        belongs_to_env = (
            session.query(EnvironmentGroup)
            .filter(EnvironmentGroup.environmentUri == environment_uri)
            .filter(EnvironmentGroup.groupUri.in_([group]))
            .count()
        )

        if not belongs_to_env:
            raise UnauthorizedOperation(
                action=permission_name,
                message=f'Team: {group} is not a member of the environment {environment_uri}',
            )
