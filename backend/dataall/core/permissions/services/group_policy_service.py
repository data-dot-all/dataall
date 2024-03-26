from dataall.core.permissions.db.group.group_policy_repositories import GroupPolicyRepository
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService


class GroupPolicyService:
    @staticmethod
    def check_group_environment_permission(session, username, groups, uri, group, permission_name):
        GroupPolicyRepository.check_group_environment_membership(
            session=session,
            username=username,
            user_groups=groups,
            group=group,
            environment_uri=uri,
            permission_name=permission_name,
        )

        ResourcePolicyService.check_user_resource_permission(
            session=session,
            username=username,
            groups=[group],
            resource_uri=uri,
            permission_name=permission_name,
        )
