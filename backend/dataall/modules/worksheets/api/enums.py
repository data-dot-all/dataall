from dataall.base.api.constants import GraphQLEnumMapper


class WorksheetRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    NoPermission = '000'
