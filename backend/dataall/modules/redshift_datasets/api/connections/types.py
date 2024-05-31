from dataall.base.api import gql

RedshiftConnection = gql.ObjectType(
    name='RedshiftConnection',
    fields=[
        gql.Field(name='connectionUri', type=gql.ID),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='connectionType', type=gql.String),
        gql.Field(name='SamlGroupName', type=gql.String),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='redshiftType', type=gql.String),
        gql.Field(name='clusterId', type=gql.String),
        gql.Field(name='nameSpaceId', type=gql.String),
        gql.Field(name='workgroupId', type=gql.String),
        gql.Field(name='redshiftUser', type=gql.String),
        gql.Field(name='secretArn', type=gql.String)
    ]
)