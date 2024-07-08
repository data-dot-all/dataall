from dataall.base.api.constants import GraphQLEnumMapper


class EnvironmentPermission(GraphQLEnumMapper):
    Owner = '999'
    Admin = '900'
    DatasetCreator = '800'
    Invited = '200'
    ProjectAccess = '050'
    NotInvited = '000'


class EnvironmentType(GraphQLEnumMapper):
    Data = 'Data'
    IntegrationTesting = 'IntegrationTesting'
