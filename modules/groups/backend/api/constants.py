from backend.api.context import GraphQLEnumMapper

class GroupMemberRole(GraphQLEnumMapper):
    Owner = 'Owner'
    Admin = 'Admin'
    Member = 'Member'
    NotMember = 'NotMember'

