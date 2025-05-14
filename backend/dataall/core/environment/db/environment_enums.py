from dataall.base.api import GraphQLEnumMapper


class PolicyManagementOptions(GraphQLEnumMapper):
    FULLY_MANAGED = 'Fully-Managed'
    PARTIALLY_MANAGED = 'Partially-Managed'
    EXTERNALLY_MANAGED = 'Externally-Managed'

class EnvironmentPrincipalType(GraphQLEnumMapper):
    GROUP = 'GROUP'
    USER = 'USER'
    ROLE = 'ROLE'

    @staticmethod
    def get_consumption_type(IAMPrincipalARN: str):
        principal_type = IAMPrincipalARN.split(":")[-1].split("/")[0]  #e.g. arn:aws:iam::account:user/user-name-with-path, arn:aws:iam::account:role/role-name-with-path
        if principal_type == 'role':
            return EnvironmentPrincipalType.ROLE.value
        if principal_type == 'user':
            return EnvironmentPrincipalType.USER.value


