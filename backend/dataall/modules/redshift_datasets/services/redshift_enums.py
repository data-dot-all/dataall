from enum import Enum
class DatashareStatus(Enum):
    """Describes the Datashare status.
    Includes possible output from https://boto3.amazonaws.com/v1/documentation/api/1.26.92/reference/services/redshift/client/describe_data_shares.html
    + NotFound + NotRegisteredInLF + MissingGlueDatabase + Completed"""
    NotFound = 'NOT_FOUND'
    PendingAuthorization = 'PENDING_AUTHORIZATION'
    Active = 'ACTIVE' # Not used in the code, but added for completeness
    Authorized = 'AUTHORIZED'
    Deauthorized = 'DEAUTHORIZED'
    Rejected = 'REJECTED'
    Available = 'AVAILABLE' # Not used in the code, but added for completeness
    NotRegisteredInLF = 'NOT_REGISTERED_IN_LF'
    MissingGlueDatabase = 'MISSING_GLUE_DATABASE'
    Completed = 'COMPLETED'

