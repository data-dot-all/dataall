from dataall.base.api.constants import GraphQLEnumMapper


class WorksheetRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    NoPermission = '000'


class WorksheetResultsFormat(GraphQLEnumMapper):
    CSV = 'csv'
    XLSX = 'xlsx'
