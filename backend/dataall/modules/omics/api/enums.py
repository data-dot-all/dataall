"""Contains the enums GraphQL mapping for Omics"""
from dataall.base.api.constants import GraphQLEnumMapper

class OmicsRunRole(GraphQLEnumMapper):
    Creator = "999"
    Admin = "900"
    NoPermission = "000"