from enum import Enum


class RedshiftDatashareStatus(Enum):
    """Describes the Datashare status.
    Includes possible output from https://boto3.amazonaws.com/v1/documentation/api/1.26.92/reference/services/redshift/client/describe_data_shares.html
    + NotFound"""

    NotFound = 'NOT_FOUND'
    PendingAuthorization = 'PENDING_AUTHORIZATION'
    Active = 'ACTIVE'
    Authorized = 'AUTHORIZED'
    Deauthorized = 'DEAUTHORIZED'
    Rejected = 'REJECTED'
    Available = 'AVAILABLE'
