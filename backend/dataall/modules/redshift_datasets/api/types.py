from dataall.base.api import gql
from dataall.modules.datasets_base.services.datasets_enums import DatasetRole

# from dataall.modules.redshift_datasets.api.resolvers import (
#     # get_dataset_environment,
#     # get_dataset_organization,
#     # get_dataset_owners_group,
#     # get_dataset_stewards_group,
#     # resolve_user_role,
#     # get_dataset_glossary_terms,
# )
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
        # TODO:ADD REDSHIFT SPECIFIC FIELDS
        # gql.Field(
        #     name='environment',
        #     type=gql.Ref('Environment'),
        #     resolver=get_dataset_environment,
        # ),
        # gql.Field(
        #     name='organization',
        #     type=gql.Ref('Organization'),
        #     resolver=get_dataset_organization,
        # ),
        # gql.Field(
        #     name='owners',
        #     type=gql.String,
        #     resolver=get_dataset_owners_group,
        # ),
        # gql.Field(
        #     name='stewards',
        #     type=gql.String,
        #     resolver=get_dataset_stewards_group,
        # ),
        # gql.Field(
        #     name='userRoleForDataset',
        #     type=DatasetRole.toGraphQLEnum(),
        #     resolver=resolve_user_role,
        # ),
        gql.Field(name='userRoleInEnvironment', type=EnvironmentPermission.toGraphQLEnum()),
        # gql.Field(
        #     name='terms',
        #     resolver=get_dataset_glossary_terms,
        #     type=gql.Ref('TermSearchResult'),
        # ),
        gql.Field(name='topics', type=gql.ArrayType(gql.Ref('Topic'))),
        gql.Field(name='confidentiality', type=gql.String),
        gql.Field(name='language', type=gql.Ref('Language')),
        gql.Field(name='autoApprovalEnabled', type=gql.Boolean),
    ],
)
