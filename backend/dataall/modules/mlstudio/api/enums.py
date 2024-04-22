"""Contains the enums GraphQL mapping for SageMaker ML Studio"""

from dataall.base.api.constants import GraphQLEnumMapper


class SagemakerStudioRole(GraphQLEnumMapper):
    """Describes the SageMaker ML Studio roles"""

    Creator = '950'
    Admin = '900'
    NoPermission = '000'
