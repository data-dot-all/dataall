"""Contains the enums GraphQL mapping for SageMaker ML Studio"""

from dataall.base.api.constants import GraphQLEnumMapper

#generation targets etc, better name : Use camelCase
class MetadataGenerationTargets(GraphQLEnumMapper):
    """Describes the s3_datasets metadata generation types"""
    Table = 'Table'
    Folder = 'Folder'
    S3_Dataset = 'S3_Dataset'

