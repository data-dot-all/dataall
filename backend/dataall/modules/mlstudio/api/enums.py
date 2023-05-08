"""Contains the enums GraphQL mapping for SageMaker ML Studio"""
from dataall.api.constants import GraphQLEnumMapper


class SagemakerStudioRole(GraphQLEnumMapper):
    """Describes the SageMaker ML Studio roles"""

    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'
