from dataall.base.api.constants import GraphQLEnumMapper


class DashboardRole(GraphQLEnumMapper):
    Creator = '999'
    Admin = '900'
    Shared = '800'
    NoPermission = '000'
