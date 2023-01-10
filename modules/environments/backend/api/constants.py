from backend.api.context import GraphQLEnumMapper

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


class RedshiftClusterRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'