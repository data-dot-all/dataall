from backend.api import GraphQLEnumMapper

class OrganisationUserRole(GraphQLEnumMapper):
    Owner = '999'
    Admin = '900'
    Member = '100'
    NotMember = '000'
    Invited = '800'


class GroupMemberRole(GraphQLEnumMapper):
    Owner = 'Owner'
    Admin = 'Admin'
    Member = 'Member'
    NotMember = 'NotMember'


class EnvironmentPermission(GraphQLEnumMapper):
    Owner = '999'
    Admin = '900'
    DatasetCreator = '800'
    Invited = '200'
    ProjectAccess = '050'
    NotInvited = '000'


class EnvironmentType(GraphQLEnumMapper):
    Data = 'Data'
    Compute = 'Compute'


class ProjectMemberRole(GraphQLEnumMapper):
    ProjectCreator = '999'
    Admin = '900'
    NotContributor = '000'

class ShareableType(GraphQLEnumMapper):
    Table = 'DatasetTable'
    StorageLocation = 'DatasetStorageLocation'
    View = 'View'


class PrincipalType(GraphQLEnumMapper):
    Any = 'Any'
    Organization = 'Organization'
    Environment = 'Environment'
    User = 'User'
    Project = 'Project'
    Public = 'Public'
    Group = 'Group'


class ShareObjectPermission(GraphQLEnumMapper):
    Approvers = '999'
    Requesters = '800'
    DatasetAdmins = '700'
    NoPermission = '000'


class ShareObjectStatus(GraphQLEnumMapper):
    Approved = 'Approved'
    Rejected = 'Rejected'
    PendingApproval = 'PendingApproval'
    Draft = 'Draft'
    Share_In_Progress = 'Share_In_Progress'
    Share_Failed = 'Share_Failed'
    Share_Succeeded = 'Share_Succeeded'
    Revoke_In_Progress = 'Revoke_In_Progress'
    Revoke_Share_Failed = 'Revoke_Share_Failed'
    Revoke_Share_Succeeded = 'Revoke_Share_Succeeded'


class ShareObjectItemAction(GraphQLEnumMapper):
    New = 'New'
    Removed = 'Removed'
