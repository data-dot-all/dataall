from dataall.base.api import gql
from dataall.modules.datasets_base.services.datasets_enums import DatasetRole

from dataall.modules.redshift_datasets.api.datasets.resolvers import (
    resolve_dataset_environment,
    resolve_dataset_organization,
    resolve_dataset_owners_group,
    resolve_dataset_stewards_group,
    resolve_user_role,
    resolve_dataset_glossary_terms,
    resolve_table_glossary_terms,
    resolve_dataset_connection,
    resolve_dataset_upvotes,
    resolve_table_dataset,
)

RedshiftDataset = gql.ObjectType(
    name='RedshiftDataset',
    fields=[
        gql.Field('datasetUri', gql.ID),
        gql.Field('label', gql.String),
        gql.Field('name', gql.String),
        gql.Field('description', gql.String),
        gql.Field('tags', gql.ArrayType(gql.String)),
        gql.Field('owner', gql.String),
        gql.Field('created', gql.String),
        gql.Field('updated', gql.String),
        gql.Field('admins', gql.ArrayType(gql.String)),
        gql.Field('AwsAccountId', gql.String),
        gql.Field('region', gql.String),
        gql.Field('SamlAdminGroupName', gql.String),
        gql.Field('imported', gql.Boolean),
        gql.Field(
            name='environment',
            type=gql.Ref('EnvironmentSimplified'),
            resolver=resolve_dataset_environment,
        ),
        gql.Field(
            name='owners',
            type=gql.String,
            resolver=resolve_dataset_owners_group,
        ),
        gql.Field(
            name='stewards',
            type=gql.String,
            resolver=resolve_dataset_stewards_group,
        ),
        gql.Field(
            name='userRoleForDataset',
            type=DatasetRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
        gql.Field(
            name='terms',
            resolver=resolve_dataset_glossary_terms,
            type=gql.Ref('TermSearchResult'),
        ),
        gql.Field('topics', gql.ArrayType(gql.Ref('Topic'))),
        gql.Field('confidentiality', gql.String),
        gql.Field('autoApprovalEnabled', gql.Boolean),
        gql.Field('schema', gql.String),
        gql.Field('upvotes', gql.Integer, resolver=resolve_dataset_upvotes),
        gql.Field(
            name='connection',
            type=gql.Ref('RedshiftConnection'),
            resolver=resolve_dataset_connection,
        ),
        gql.Field('addedTables', gql.Ref('RedshiftAddTableResult')),
    ],
)

RedshiftDatasetTable = gql.ObjectType(
    name='RedshiftDatasetTable',
    fields=[
        gql.Field('rsTableUri', gql.ID),
        gql.Field('datasetUri', gql.String),
        gql.Field('label', gql.String),
        gql.Field('name', gql.String),
        gql.Field('description', gql.String),
        gql.Field('owner', gql.String),
        gql.Field('created', gql.String),
        gql.Field('updated', gql.String),
        gql.Field('region', gql.String),
        gql.Field('tags', gql.ArrayType(gql.String)),
        gql.Field(
            name='terms',
            resolver=resolve_table_glossary_terms,
            type=gql.Ref('TermSearchResult'),
        ),
        gql.Field('dataset', gql.Ref('RedshiftDataset'), resolver=resolve_table_dataset),
    ],
)

RedshiftDatasetTableListItem = gql.ObjectType(
    name='RedshiftDatasetTableListItem',
    fields=[
        gql.Field('rsTableUri', gql.ID),
        gql.Field('datasetUri', gql.String),
        gql.Field('label', gql.String),
        gql.Field('name', gql.String),
        gql.Field('description', gql.String),
        gql.Field('owner', gql.String),
        gql.Field('created', gql.String),
        gql.Field('updated', gql.String),
        gql.Field('region', gql.String),
        gql.Field('tags', gql.ArrayType(gql.String)),
    ],
)

RedshiftDatasetTableSearchResult = gql.ObjectType(
    name='RedshiftDatasetTableSearchResult',
    fields=[
        gql.Field('nodes', gql.ArrayType(RedshiftDatasetTableListItem)),
        gql.Field('count', gql.Integer),
        gql.Field('pages', gql.Integer),
        gql.Field('page', gql.Integer),
        gql.Field('hasNext', gql.Boolean),
        gql.Field('hasPrevious', gql.Boolean),
    ],
)

RedshiftDatasetTableColumn = gql.ObjectType(
    name='RedshiftDatasetTableColumn',
    fields=[
        gql.Field('columnDefault', gql.String),
        gql.Field('isCaseSensitive', gql.Boolean),
        gql.Field('isCurrency', gql.Boolean),
        gql.Field('isSigned', gql.Boolean),
        gql.Field('label', gql.String),
        gql.Field('length', gql.Integer),
        gql.Field('name', gql.String),
        gql.Field('nullable', gql.Boolean),
        gql.Field('precision', gql.Integer),
        gql.Field('scale', gql.Integer),
        gql.Field('typeName', gql.String),
    ],
)

RedshiftDatasetTableColumnSearchResult = gql.ObjectType(
    name='RedshiftDatasetTableColumnSearchResult',
    fields=[
        gql.Field('nodes', gql.ArrayType(RedshiftDatasetTableColumn)),
        gql.Field('count', gql.Integer),
        gql.Field('pages', gql.Integer),
        gql.Field('page', gql.Integer),
        gql.Field('hasNext', gql.Boolean),
        gql.Field('hasPrevious', gql.Boolean),
    ],
)

RedshiftAddTableResult = gql.ObjectType(
    name='RedshiftAddTableResult',
    fields=[gql.Field('successTables', gql.ArrayType(gql.String)), gql.Field('errorTables', gql.ArrayType(gql.String))],
)
