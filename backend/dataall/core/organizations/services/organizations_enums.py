from dataall.base.api.constants import GraphQLEnumMapper


class OrganisationUserRole(GraphQLEnumMapper):
    Owner = '999'
    Admin = '900'
    Member = '100'
    NotMember = '000'
    Invited = '800'
