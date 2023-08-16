from dataall.base.api.constants import GraphQLEnumMapper


class GlossaryRole(GraphQLEnumMapper):
    # Permissions on a glossary
    Admin = '900'
    NoPermission = '000'
