from dataall.core.permissions.db.group.group_policy_repositories import GroupPolicyRepository
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.base.db.exceptions import UnauthorizedOperation
from functools import wraps
from dataall.base.context import get_context


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
    def check_group_environment_permission(uri, group, permission_name):
        context = get_context()
        username = context.username
        groups = context.groups

        with context.db_engine.scoped_session() as session:
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

    @staticmethod
    def has_group_permission(permission):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                if 'uri' not in kwargs:
                    raise KeyError(f"{f.__name__} doesn't have parameter uri")
                uri = kwargs['uri']

                if 'admin_group' not in kwargs:
                    raise KeyError(f"{f.__name__} doesn't have parameter admin_group")
                admin_group = kwargs['admin_group']

                GroupPolicyService.check_group_environment_permission(
                    uri=uri,
                    group=admin_group,
                    permission_name=permission,
                )

                return f(*args, **kwargs)

            return wrapper

        return decorator
