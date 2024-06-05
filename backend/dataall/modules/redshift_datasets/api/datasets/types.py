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
    resolve_datashare_state,
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
        gql.Field(name='includePattern', type=gql.String),
        gql.Field(name='excludePattern', type=gql.String),
        gql.Field(name='datashareArn', type=gql.String),
        gql.Field(name='datashareStatus', type=gql.String, resolver=resolve_datashare_state),
        gql.Field(name='upvotes', type=gql.Integer, resolver=resolve_dataset_upvotes),
        gql.Field(
            name='connection',
            type=gql.Ref('RedshiftConnection'),
            resolver=resolve_dataset_connection,
        ),
    ],
)
