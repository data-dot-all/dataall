from dataall.base.api import gql
from dataall.modules.metadata_forms.api.resolvers import get_home_entity_name

MetadataForm = gql.ObjectType(
    name='MetadataForm',
    fields=[
        gql.Field(name='uri', type=gql.ID),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='SamlGroupName', type=gql.String),
        gql.Field(name='visibility', type=gql.String),
        gql.Field(name='homeEntity', type=gql.String),
        gql.Field(name='homeEntityName', type=gql.String, resolver=get_home_entity_name),
    ],
)

MetadataFormSearchResult = gql.ObjectType(
    name='MetadataFormSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='nodes', type=gql.ArrayType(gql.Ref('MetadataForm'))),
        gql.Field(name='pageSize', type=gql.Integer),
        gql.Field(name='nextPage', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='previousPage', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
    ],
)
