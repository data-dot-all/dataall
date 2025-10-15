from dataall.base.api import GraphQLEnumMapper


class EnvironmentIAMPrincipalType(GraphQLEnumMapper):
    GROUP = 'GROUP'
    USER = 'USER'
    ROLE = 'ROLE'

    @staticmethod
    def get_consumption_type(IAMPrincipalARN: str):
        principal_type = IAMPrincipalARN.split(':')[-1].split('/')[
            0
        ]  # e.g. arn:aws:iam::account:user/user-name-with-path, arn:aws:iam::account:role/role-name-with-path
        if principal_type == 'role':
            return EnvironmentIAMPrincipalType.ROLE.value
        if principal_type == 'user':
            return EnvironmentIAMPrincipalType.USER.value


class EnvironmentIAMPrincipalAttachmentStatus(GraphQLEnumMapper):
    NOTAPPLICABLE = 'N/A'
    ATTACHED = 'Attached'
    NOTATTACHED = 'Not-Attached'

    @staticmethod
    def get_policy_attachment_type(is_attached: bool):
        return (
            EnvironmentIAMPrincipalAttachmentStatus.ATTACHED.value
            if is_attached
            else EnvironmentIAMPrincipalAttachmentStatus.NOTATTACHED.value
        )
