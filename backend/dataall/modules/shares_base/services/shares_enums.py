from dataall.base.api.constants import GraphQLEnumMapper


class ShareableType(GraphQLEnumMapper):
    Table = 'DatasetTable'
    StorageLocation = 'DatasetStorageLocation'
    S3Bucket = 'S3Bucket'
    RedshiftTable = 'RedshiftTable'


class ShareObjectPermission(GraphQLEnumMapper):
    Approvers = '999'
    ApproversAndRequesters = '900'
    Requesters = '800'
    DatasetAdmins = '700'
    NoPermission = '000'


class ShareObjectDataPermission(GraphQLEnumMapper):
    Read = 'Read'
    Write = 'Write'
    Modify = 'Modify'


class ShareObjectStatus(GraphQLEnumMapper):
    Deleted = 'Deleted'
    Approved = 'Approved'
    Rejected = 'Rejected'
    Revoked = 'Revoked'
    Draft = 'Draft'
    Submitted = 'Submitted'
    Submitted_For_Extension = 'Submitted_For_Extension'
    Extension_Rejected = 'Extension_Rejected'
    Revoke_In_Progress = 'Revoke_In_Progress'
    Share_In_Progress = 'Share_In_Progress'
    Processed = 'Processed'


class ShareItemStatus(GraphQLEnumMapper):
    Deleted = 'Deleted'
    PendingApproval = 'PendingApproval'
    PendingExtension = 'PendingExtension'
    Share_Approved = 'Share_Approved'
    Share_Rejected = 'Share_Rejected'
    Share_In_Progress = 'Share_In_Progress'
    Share_Succeeded = 'Share_Succeeded'
    Share_Failed = 'Share_Failed'
    Revoke_Approved = 'Revoke_Approved'
    Revoke_In_Progress = 'Revoke_In_Progress'
    Revoke_Failed = 'Revoke_Failed'
    Revoke_Succeeded = 'Revoke_Succeeded'


class ShareItemHealthStatus(GraphQLEnumMapper):
    Healthy = 'Healthy'
    Unhealthy = 'Unhealthy'
    PendingVerify = 'PendingVerify'
    PendingReApply = 'PendingReApply'


class ShareObjectActions(GraphQLEnumMapper):
    Create = 'Create'
    Submit = 'Submit'
    Approve = 'Approve'
    Reject = 'Reject'
    RevokeItems = 'RevokeItems'
    Start = 'Start'
    Finish = 'Finish'
    FinishPending = 'FinishPending'
    Delete = 'Delete'
    Extension = 'Extension'
    ExtensionApprove = 'ExtensionApprove'
    ExtensionReject = 'ExtensionReject'
    CancelExtension = 'CancelExtension'


class ShareItemActions(GraphQLEnumMapper):
    AddItem = 'AddItem'
    RemoveItem = 'RemoveItem'
    Failure = 'Failure'
    Success = 'Success'


class PrincipalType(GraphQLEnumMapper):
    Group = 'Group'
    ConsumptionRole = 'ConsumptionRole'
    RedshiftRole = 'RedshiftRole'


class ShareSortField(GraphQLEnumMapper):
    created = 'created'
    updated = 'updated'
    label = 'label'
