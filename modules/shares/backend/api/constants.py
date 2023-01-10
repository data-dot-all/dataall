from backend.api.context import GraphQLEnumMapper

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

