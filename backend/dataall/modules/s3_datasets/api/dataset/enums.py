"""Contains the enums GraphQL mapping for SageMaker ML Studio"""

from dataall.base.api.constants import GraphQLEnumMapper


class s3_datasets(GraphQLEnumMapper):
    """Describes the s3_datasets metadata generation types"""
    Table = 'Table'
    Folder = 'Folder'
