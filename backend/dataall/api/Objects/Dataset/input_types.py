from ... import gql
from ....api.constants import GraphQLEnumMapper, SortDirection


class DatasetSortField(GraphQLEnumMapper):
    label = 'label'
    created = 'created'
    updated = 'updated'


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
        gql.Argument(
            name='businessOwnerDelegationEmails', type=gql.ArrayType(gql.String)
        ),
        gql.Argument('confidentiality', gql.Ref('ConfidentialityClassification')),
        gql.Argument(name='stewards', type=gql.String),
        gql.Argument('lfTagKey', type=gql.String),
        gql.Argument(name='lfTagValue', type=gql.String),
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
        gql.Argument('confidentiality', gql.Ref('ConfidentialityClassification')),
        gql.Argument(name='stewards', type=gql.String),
    ],
)

DatasetSortCriteria = gql.InputType(
    name='DatasetSortCriteria',
    arguments=[
        gql.Argument(
            name='field', type=gql.NonNullableType(DatasetSortField.toGraphQLEnum())
        ),
        gql.Argument(name='direction', type=SortDirection.toGraphQLEnum()),
    ],
)


DatasetFilter = gql.InputType(
    name='DatasetFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('roles', gql.ArrayType(gql.Ref('DatasetRole'))),
        gql.Argument('InProject', gql.String),
        gql.Argument('notInProject', gql.String),
        gql.Argument('displayArchived', gql.Boolean),
        # gql.Argument("organization", gql.String),
        # gql.Argument("environment", gql.String),
        gql.Argument('sort', gql.ArrayType(DatasetSortCriteria)),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
    ],
)

DatasetPresignedUrlInput = gql.InputType(
    name='DatasetPresignedUrlInput',
    arguments=[
        gql.Field(name='fileName', type=gql.String),
        gql.Field(name='prefix', type=gql.String),
    ],
)


CrawlerInput = gql.InputType(
    name='CrawlerInput', arguments=[gql.Argument(name='prefix', type=gql.String)]
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
        gql.Argument('KmsKeyId', gql.String),
        gql.Argument('adminRoleName', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('owner', gql.NonNullableType(gql.String)),
        gql.Argument('language', gql.Ref('Language')),
        gql.Argument('topics', gql.ArrayType(gql.Ref('Topic'))),
        gql.Argument(name='SamlAdminGroupName', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='businessOwnerEmail', type=gql.String),
        gql.Argument(
            name='businessOwnerDelegationEmails', type=gql.ArrayType(gql.String)
        ),
        gql.Argument('confidentiality', gql.Ref('ConfidentialityClassification')),
        gql.Argument(name='stewards', type=gql.String),
    ],
)
