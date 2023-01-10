from backend.api.context import GraphQLEnumMapper

class WorksheetRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    SharedWithWritePermission = '500'
    SharedWithReadPermission = '400'
    NoPermission = '000'

