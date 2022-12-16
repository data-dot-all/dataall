"""
    1) i created it								DatasetCreator
    2) i belong to the Dataset Admin group		DatasetAdmin
    3) i'm the busoness owner					DatasetBusinessOwner
    4) i'm a steward 							DatasetSteward
    5) it's shared with one of My Env			Shared
    6) no permission at all						NoPermission
"""


from enum import Enum
from . import gql


class GraphQLEnumMapper(Enum):
    @classmethod
    def toGraphQLEnum(cls):
        return gql.Enum(name=cls.__name__, values=cls)

    @classmethod
    def to_value(cls, label):
        for c in cls:
            if c.name == label:
                return c.value
        return None

    @classmethod
    def to_label(cls, value):
        for c in cls:
            if getattr(cls, c.name).value == value:
                return c.name
        return None


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


class DashboardRole(GraphQLEnumMapper):
    Creator = '999'
    Admin = '900'
    Shared = '800'
    NoPermission = '000'


class DataPipelineRole(GraphQLEnumMapper):
    Creator = '999'
    Admin = '900'
    NoPermission = '000'


class DatasetRole(GraphQLEnumMapper):
    # Permissions on a dataset
    BusinessOwner = '999'
    DataSteward = '998'
    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'


class GlossaryRole(GraphQLEnumMapper):
    # Permissions on a glossary
    Admin = '900'
    NoPermission = '000'


class RedshiftClusterRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'


class ScheduledQueryRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'


class SagemakerNotebookRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'


class SagemakerStudioRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'


class AirflowClusterRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'


class SortDirection(GraphQLEnumMapper):
    asc = 'asc'
    desc = 'desc'


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
    ConsumptionRole = 'ConsumptionRole'


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


class ConfidentialityClassification(GraphQLEnumMapper):
    Unclassified = 'Unclassified'
    Official = 'Official'
    Secret = 'Secret'


class Language(GraphQLEnumMapper):
    English = 'English'
    French = 'French'
    German = 'German'


class Topic(GraphQLEnumMapper):
    Finances = 'Finances'
    HumanResources = 'HumanResources'
    Products = 'Products'
    Services = 'Services'
    Operations = 'Operations'
    Research = 'Research'
    Sales = 'Sales'
    Orders = 'Orders'
    Sites = 'Sites'
    Energy = 'Energy'
    Customers = 'Customers'
    Misc = 'Misc'


class WorksheetRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    SharedWithWritePermission = '500'
    SharedWithReadPermission = '400'
    NoPermission = '000'


GLUEBUSINESSPROPERTIES = ['EXAMPLE_GLUE_PROPERTY_TO_BE_ADDED_ON_ES']
