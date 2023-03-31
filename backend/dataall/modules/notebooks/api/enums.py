"""Contains the enums GraphQL mapping for SageMaker notebooks """
from dataall.api.constants import GraphQLEnumMapper


class SagemakerNotebookRole(GraphQLEnumMapper):
    """Describes the SageMaker Notebook roles"""

    CREATOR = "950"
    ADMIN = "900"
    SHARED = "300"
    NO_PERMISSION = "000"
