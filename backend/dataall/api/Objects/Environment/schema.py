from .resolvers import *
from ...constants import EnvironmentPermission

EnvironmentUserPermission = gql.ObjectType(
    name='EnvironmentUserPermission',
    fields=[
        gql.Field(name='userName', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='userRoleInEnvironment', type=gql.Ref('EnvironmentPermission')),
    ],
)

EnvironmentUserPermissionSearchResult = gql.ObjectType(
    name='EnvironmentUserPermissionSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='nodes', type=gql.ArrayType(EnvironmentUserPermission)),
    ],
)


EnvironmentGroupPermission = gql.ObjectType(
    name='EnvironmentGroupPermission',
    fields=[
        gql.Field(name='groupUri', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(
            name='groupRoleInEnvironment', type=EnvironmentPermission.toGraphQLEnum()
        ),
        gql.Field(name='Group', type=gql.Ref('Group')),
    ],
)

EnvironmentGroupPermissionSearchResult = gql.ObjectType(
    name='EnvironmentGroupPermissionSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='nodes', type=gql.ArrayType(EnvironmentGroupPermission)),
    ],
)


Environment = gql.ObjectType(
    name='Environment',
    fields=[
        gql.Field(name='environmentUri', type=gql.ID),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='deleted', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='admins', type=gql.ArrayType(gql.String)),
        gql.Field(name='environmentType', type=gql.String),
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='SamlGroupName', type=gql.String),
        gql.Field(name='resourcePrefix', type=gql.String),
        gql.Field(name='EnvironmentDefaultIAMRoleArn', type=gql.String),
        gql.Field(name='EnvironmentDefaultIAMRoleName', type=gql.String),
        gql.Field(name='EnvironmentDefaultIAMRoleImported', type=gql.Boolean),
        gql.Field(name='datasets', type=gql.String),
        gql.Field(
            name='organization',
            type=gql.Ref('Organization'),
            resolver=get_parent_organization,
        ),
        gql.Field(
            'userRoleInEnvironment',
            type=EnvironmentPermission.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
        gql.Field('validated', type=gql.Boolean),
        gql.Field('dashboardsEnabled', type=gql.Boolean),
        gql.Field('notebooksEnabled', type=gql.Boolean),
        gql.Field('mlStudiosEnabled', type=gql.Boolean),
        gql.Field('pipelinesEnabled', type=gql.Boolean),
        gql.Field('warehousesEnabled', type=gql.Boolean),
        gql.Field('roleCreated', type=gql.Boolean),
        gql.Field('isOrganizationDefaultEnvironment', type=gql.Boolean),
        gql.Field('stack', type=gql.Ref('Stack'), resolver=get_environment_stack),
        gql.Field('subscriptionsEnabled', type=gql.Boolean),
        gql.Field('subscriptionsProducersTopicImported', type=gql.Boolean),
        gql.Field('subscriptionsConsumersTopicImported', type=gql.Boolean),
        gql.Field('subscriptionsConsumersTopicName', type=gql.String),
        gql.Field('subscriptionsProducersTopicName', type=gql.String),
        gql.Field('EnvironmentDefaultBucketName', type=gql.String),
        gql.Field('EnvironmentDefaultAthenaWorkGroup', type=gql.String),
        gql.Field(
            name='networks',
            type=gql.ArrayType(gql.Ref('Vpc')),
            resolver=resolve_vpc_list,
        ),
    ],
)


EnvironmentSearchResult = gql.ObjectType(
    name='EnvironmentSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='nodes', type=gql.ArrayType(Environment)),
        gql.Field(name='pageSize', type=gql.Integer),
        gql.Field(name='nextPage', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='previousPage', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
    ],
)


EnvironmentPublishedItem = gql.ObjectType(
    name='EnvironmentPublishedItem',
    fields=[
        gql.Field(name='shareUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='datasetName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='itemAccess', type=gql.NonNullableType(gql.String)),
        gql.Field(name='itemType', type=gql.NonNullableType(gql.String)),
        gql.Field(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='principalId', type=gql.NonNullableType(gql.String)),
        gql.Field(name='environmentName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='organizationUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='organizationName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='created', type=gql.NonNullableType(gql.String)),
        gql.Field(name='GlueDatabaseName', type=gql.String),
        gql.Field(name='GlueTableName', type=gql.String),
        gql.Field(name='S3AccessPointName', type=gql.String),
    ],
)


EnvironmentPublishedItemSearchResults = gql.ObjectType(
    name='EnvironmentPublishedItemSearchResults',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(EnvironmentPublishedItem)),
    ],
)

ConsumptionRole = gql.ObjectType(
    name='ConsumptionRole',
    fields=[
        gql.Field(name='consumptionRoleUri', type=gql.String),
        gql.Field(name='consumptionRoleName', type=gql.String),
        gql.Field(name='groupUri', type=gql.String),
        gql.Field(name='environmentUri', type=gql.String),
        gql.Field(name='IAMRoleArn', type=gql.String),
        gql.Field(name='IAMRoleName', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='deleted', type=gql.String),
    ],
)

ConsumptionRoleSearchResult = gql.ObjectType(
    name='ConsumptionRoleSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(ConsumptionRole)),
    ],
)
