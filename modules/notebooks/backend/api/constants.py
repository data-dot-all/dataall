from backend.api import GraphQLEnumMapper


class SagemakerNotebookRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'

