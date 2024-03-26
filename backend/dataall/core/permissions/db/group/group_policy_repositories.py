from dataall.core.environment.db.environment_models import EnvironmentGroup
from dataall.base.db.exceptions import UnauthorizedOperation


class GroupPolicyRepository:
    """Checks permission of environment group"""

    @staticmethod
    def check_group_environment_membership(session, environment_uri, group, username, user_groups, permission_name):
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
