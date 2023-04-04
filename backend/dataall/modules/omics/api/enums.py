"""Contains the enums GraphQL mapping for Omics """
from dataall.api.constants import GraphQLEnumMapper


class OmicsProjectRole(GraphQLEnumMapper):
    """Describes the Omics project roles"""

    CREATOR = "950"
    ADMIN = "900"
    SHARED = "300"
    NO_PERMISSION = "000"
