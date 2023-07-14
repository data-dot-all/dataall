from enum import Enum


class ShareObjectStatus(Enum):
    Deleted = 'Deleted'
    Approved = 'Approved'
    Rejected = 'Rejected'
    Revoked = 'Revoked'
    Draft = 'Draft'
    Submitted = 'Submitted'
    Revoke_In_Progress = 'Revoke_In_Progress'
    Share_In_Progress = 'Share_In_Progress'
    Processed = 'Processed'


class ShareObjectPermission(Enum):
    Approvers = '999'
    Requesters = '800'
    DatasetAdmins = '700'
    NoPermission = '000'


class ShareItemStatus(Enum):
    Deleted = 'Deleted'
    PendingApproval = 'PendingApproval'
    Share_Approved = 'Share_Approved'
    Share_Rejected = 'Share_Rejected'
    Share_In_Progress = 'Share_In_Progress'
    Share_Succeeded = 'Share_Succeeded'
    Share_Failed = 'Share_Failed'
    Revoke_Approved = 'Revoke_Approved'
    Revoke_In_Progress = 'Revoke_In_Progress'
    Revoke_Failed = 'Revoke_Failed'
    Revoke_Succeeded = 'Revoke_Succeeded'


class ShareObjectActions(Enum):
    Submit = 'Submit'
    Approve = 'Approve'
    Reject = 'Reject'
    RevokeItems = 'RevokeItems'
    Start = 'Start'
    Finish = 'Finish'
    FinishPending = 'FinishPending'
    Delete = 'Delete'


class ShareItemActions(Enum):
    AddItem = 'AddItem'
    RemoveItem = 'RemoveItem'
    Failure = 'Failure'
    Success = 'Success'


class ShareableType(Enum):
    Table = 'DatasetTable'
    StorageLocation = 'DatasetStorageLocation'
    View = 'View'
