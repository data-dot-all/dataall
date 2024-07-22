from dataall.base.api import gql
from dataall.modules.datasets_base.services.datasets_enums import DatasetRole

from dataall.modules.redshift_datasets.api.datasets.resolvers import (
    resolve_dataset_environment,
    resolve_dataset_organization,
    resolve_dataset_owners_group,
    resolve_dataset_stewards_group,
    resolve_user_role,
    resolve_dataset_glossary_terms,
    resolve_dataset_connection,
    resolve_dataset_upvotes,
)
from dataall.core.environment.api.enums import EnvironmentPermission


RedshiftDataset = gql.ObjectType(
    name='RedshiftDataset',
    fields=[
        gql.Field(name='datasetUri', type=gql.ID),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='admins', type=gql.ArrayType(gql.String)),
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='SamlAdminGroupName', type=gql.String),
        gql.Field(name='businessOwnerEmail', type=gql.String),
        gql.Field(name='businessOwnerDelegationEmails', type=gql.ArrayType(gql.String)),
        gql.Field(name='imported', type=gql.Boolean),
        gql.Field(
            name='environment',
            type=gql.Ref('Environment'),
            resolver=resolve_dataset_environment,
        ),
        gql.Field(
            name='organization',
            type=gql.Ref('Organization'),
            resolver=resolve_dataset_organization,
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
        gql.Field(name='userRoleInEnvironment', type=EnvironmentPermission.toGraphQLEnum()),
        gql.Field(
            name='terms',
            resolver=resolve_dataset_glossary_terms,
            type=gql.Ref('TermSearchResult'),
        ),
        gql.Field(name='topics', type=gql.ArrayType(gql.Ref('Topic'))),
        gql.Field(name='confidentiality', type=gql.String),
        gql.Field(name='language', type=gql.Ref('Language')),
        gql.Field(name='autoApprovalEnabled', type=gql.Boolean),
        gql.Field(name='schema', type=gql.String),
        gql.Field(name='upvotes', type=gql.Integer, resolver=resolve_dataset_upvotes),
        gql.Field(
            name='connection',
            type=gql.Ref('RedshiftConnection'),
            resolver=resolve_dataset_connection,
        ),
    ],
)

RedshiftDatasetTable = gql.ObjectType(
    name='RedshiftDatasetTable',
    fields=[
        gql.Field(name='name', type=gql.String),
        gql.Field(name='type', type=gql.String),
        gql.Field(name='alreadyAdded', type=gql.String),
    ],
)

RedshiftDatasetTableListItem = gql.ObjectType(
    name='RedshiftDatasetTableListItem',
    fields=[
        gql.Field(name='rsTableUri', type=gql.ID),
        gql.Field(name='datasetUri', type=gql.String),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
    ],
)

RedshiftDatasetTableSearchResult = gql.ObjectType(
    name='RedshiftDatasetTableSearchResult',
    fields=[
        gql.Field(name='nodes', type=gql.ArrayType(RedshiftDatasetTableListItem)),
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
    ],
)

RedshiftDatasetTableColumn = gql.ObjectType(
    name='RedshiftDatasetTableColumn',
    fields=[
        gql.Field(name='columnDefault', type=gql.String),
        gql.Field(name='isCaseSensitive', type=gql.Boolean),
        gql.Field(name='isCurrency', type=gql.Boolean),
        gql.Field(name='isSigned', type=gql.Boolean),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='length', type=gql.Integer),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='nullable', type=gql.Boolean),
        gql.Field(name='precision', type=gql.Integer),
        gql.Field(name='scale', type=gql.Integer),
        gql.Field(name='typeName', type=gql.String),
    ],
)

RedshiftDatasetTableColumnSearchResult = gql.ObjectType(
    name='RedshiftDatasetTableColumnSearchResult',
    fields=[
        gql.Field(name='nodes', type=gql.ArrayType(RedshiftDatasetTableColumn)),
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
    ],
)
