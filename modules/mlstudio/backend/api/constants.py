from backend.api.context import GraphQLEnumMapper

class SagemakerStudioRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'

