from dataall.base.api import gql


NewDatasetInput = gql.InputType(
    name='NewDatasetInput',
    arguments=[
        gql.Argument('label', gql.NonNullableType(gql.String)),
        gql.Argument('organizationUri', gql.NonNullableType(gql.String)),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('description', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('owner', gql.String),
        gql.Argument('language', gql.Ref('Language')),
        gql.Argument('topics', gql.ArrayType(gql.Ref('Topic'))),
        gql.Argument(name='SamlAdminGroupName', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='businessOwnerEmail', type=gql.String),
        gql.Argument(name='businessOwnerDelegationEmails', type=gql.ArrayType(gql.String)),
        gql.Argument('confidentiality', gql.String),
        gql.Argument(name='stewards', type=gql.String),
        gql.Argument(name='autoApprovalEnabled', type=gql.Boolean),
    ],
)

ModifyDatasetInput = gql.InputType(
    name='ModifyDatasetInput',
    arguments=[
        gql.Argument('label', gql.String),
        gql.Argument('description', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('topics', gql.ArrayType(gql.Ref('Topic'))),
        gql.Argument('terms', gql.ArrayType(gql.String)),
        gql.Argument('businessOwnerDelegationEmails', gql.ArrayType(gql.String)),
        gql.Argument('businessOwnerEmail', gql.String),
        gql.Argument('language', gql.Ref('Language')),
        gql.Argument('confidentiality', gql.String),
        gql.Argument(name='stewards', type=gql.String),
        gql.Argument('KmsAlias', gql.NonNullableType(gql.String)),
        gql.Argument(name='autoApprovalEnabled', type=gql.Boolean),
    ],
)
DatasetMetadataInput = gql.InputType(
    name='DatasetMetadataInput',
    arguments=[
        gql.Argument('label', gql.String),
        gql.Argument('description', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('topics', gql.ArrayType(gql.Ref('Topic'))),
        
    ],
)

DatasetPresignedUrlInput = gql.InputType(
    name='DatasetPresignedUrlInput',
    arguments=[
        gql.Field(name='fileName', type=gql.String),
        gql.Field(name='prefix', type=gql.String),
    ],
)


CrawlerInput = gql.InputType(name='CrawlerInput', arguments=[gql.Argument(name='prefix', type=gql.String)])
SampleDataInput = gql.InputType(
    name='SampleDataInput',
    arguments=[
        gql.Field(name='fields', type=gql.ArrayType(gql.String)),
        gql.Field(name='rows', type=gql.ArrayType(gql.String)),
    ],
)
ImportDatasetInput = gql.InputType(
    name='ImportDatasetInput',
    arguments=[
        gql.Argument('label', gql.NonNullableType(gql.String)),
        gql.Argument('organizationUri', gql.NonNullableType(gql.String)),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('description', gql.String),
        gql.Argument('bucketName', gql.NonNullableType(gql.String)),
        gql.Argument('glueDatabaseName', gql.String),
        gql.Argument('KmsKeyAlias', gql.NonNullableType(gql.String)),
        gql.Argument('adminRoleName', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('owner', gql.NonNullableType(gql.String)),
        gql.Argument('language', gql.Ref('Language')),
        gql.Argument('topics', gql.ArrayType(gql.Ref('Topic'))),
        gql.Argument(name='SamlAdminGroupName', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='businessOwnerEmail', type=gql.String),
        gql.Argument(name='businessOwnerDelegationEmails', type=gql.ArrayType(gql.String)),
        gql.Argument('confidentiality', gql.String),
        gql.Argument(name='stewards', type=gql.String),
        gql.Argument(name='autoApprovalEnabled', type=gql.Boolean),
    ],
)

ShareObjectSelectorInput = gql.InputType(
    name='ShareObjectSelectorInput',
    arguments=[
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='shareUris', type=gql.NonNullableType(gql.ArrayType(gql.String))),
    ],
)
