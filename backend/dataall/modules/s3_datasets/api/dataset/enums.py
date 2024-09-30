from dataall.base.api.constants import GraphQLEnumMapper


class MetadataGenerationTargets(GraphQLEnumMapper):
    """Describes the s3_datasets metadata generation types"""

    Table = 'Table'
    Folder = 'Folder'
    S3_Dataset = 'S3_Dataset'
