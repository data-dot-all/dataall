from dataall.api.constants import GraphQLEnumMapper


class DataPipelineRole(GraphQLEnumMapper):
    Creator = '999'
    Admin = '900'
    NoPermission = '000'