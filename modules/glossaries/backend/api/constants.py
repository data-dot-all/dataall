from backend.api.context import GraphQLEnumMapper

class GlossaryRole(GraphQLEnumMapper):
    Admin = '900'
    NoPermission = '000'

