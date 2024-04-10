from dataall.core.permissions.db.group.group_policy_repositories import GroupPolicyRepository
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.base.db.exceptions import UnauthorizedOperation


class GroupPolicyRequestValidationService:
    @staticmethod
    def validate_team_member(username, user_groups, group, permission_name):
        if group and group not in user_groups:
            raise UnauthorizedOperation(
                action=permission_name,
                message=f'User: {username} is not a member of the team {group}',
            )


class GroupPolicyService:
    @staticmethod
    def check_group_environment_permission(session, username, groups, uri, group, permission_name):
        GroupPolicyRequestValidationService.validate_team_member(
            username=username, user_groups=groups, group=group, permission_name=permission_name
        )

        if not GroupPolicyRepository.check_group_environment_membership(
            session=session,
            group=group,
            environment_uri=uri,
        ):
            raise UnauthorizedOperation(
                action=permission_name,
                message=f'Team: {group} is not a member of the environment {uri}',
            )

        ResourcePolicyService.check_user_resource_permission(
            session=session,
            username=username,
            groups=[group],
            resource_uri=uri,
            permission_name=permission_name,
        )
