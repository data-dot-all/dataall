from dataall.core.environment.db.environment_models import EnvironmentGroup
from dataall.base.db.exceptions import UnauthorizedOperation


class GroupPolicyRepository:
    """Checks permission of environment group"""

    @staticmethod
    def check_group_environment_membership(session, environment_uri, group):
        belongs_to_env = (
            session.query(EnvironmentGroup)
            .filter(EnvironmentGroup.environmentUri == environment_uri)
            .filter(EnvironmentGroup.groupUri.in_([group]))
            .count()
        )

        return belongs_to_env > 0
