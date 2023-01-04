from ... import gql
from ....api.constants import GraphQLEnumMapper, SortDirection


AwsEnvironmentInput = gql.InputType(
    name='AwsEnvironmentInput',
    arguments=[
        gql.Argument('AwsAccountId', gql.NonNullableType(gql.String)),
        gql.Argument('region', gql.NonNullableType(gql.String)),
    ],
)

NewEnvironmentInput = gql.InputType(
    name='NewEnvironmentInput',
    arguments=[
        gql.Argument('label', gql.NonNullableType(gql.String)),
        gql.Argument('organizationUri', gql.NonNullableType(gql.String)),
        gql.Argument('SamlGroupName', gql.NonNullableType(gql.String)),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('description', gql.String),
        gql.Argument('AwsAccountId', gql.NonNullableType(gql.String)),
        gql.Argument('region', gql.NonNullableType(gql.String)),
        gql.Argument('dashboardsEnabled', type=gql.Boolean),
        gql.Argument('notebooksEnabled', type=gql.Boolean),
        gql.Argument('mlStudiosEnabled', type=gql.Boolean),
        gql.Argument('pipelinesEnabled', type=gql.Boolean),
        gql.Argument('warehousesEnabled', type=gql.Boolean),
        gql.Argument('vpcId', gql.String),
        gql.Argument('privateSubnetIds', gql.ArrayType(gql.String)),
        gql.Argument('publicSubnetIds', gql.ArrayType(gql.String)),
        gql.Argument('EnvironmentDefaultIAMRoleName', gql.String),
        gql.Argument('resourcePrefix', gql.String),
    ],
)

ModifyEnvironmentInput = gql.InputType(
    name='ModifyEnvironmentInput',
    arguments=[
        gql.Argument('label', gql.String),
        gql.Argument('description', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('SamlGroupName', gql.String),
        gql.Argument('vpcId', gql.String),
        gql.Argument('privateSubnetIds', gql.ArrayType(gql.String)),
        gql.Argument('publicSubnetIds', gql.ArrayType(gql.String)),
        gql.Argument('dashboardsEnabled', type=gql.Boolean),
        gql.Argument('notebooksEnabled', type=gql.Boolean),
        gql.Argument('mlStudiosEnabled', type=gql.Boolean),
        gql.Argument('pipelinesEnabled', type=gql.Boolean),
        gql.Argument('warehousesEnabled', type=gql.Boolean),
        gql.Argument('resourcePrefix', gql.String),
    ],
)

EnableDataSubscriptionsInput = gql.InputType(
    name='EnableDataSubscriptionsInput',
    arguments=[
        gql.Argument('producersTopicArn', gql.String),
    ],
)


class EnvironmentSortField(GraphQLEnumMapper):
    created = 'created'
    label = 'label'


EnvironmentSortCriteria = gql.InputType(
    name='EnvironmentSortCriteria',
    arguments=[
        gql.Argument(
            name='field', type=gql.NonNullableType(EnvironmentSortField.toGraphQLEnum())
        ),
        gql.Argument(
            name='direction', type=gql.NonNullableType(SortDirection.toGraphQLEnum())
        ),
    ],
)

EnvironmentFilter = gql.InputType(
    name='EnvironmentFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('page', gql.Integer),
        gql.Argument('displayArchived', gql.Boolean),
        gql.Argument('roles', gql.ArrayType(gql.Ref('EnvironmentPermission'))),
        gql.Argument('quicksight', gql.Boolean),
        gql.Argument('sort', gql.ArrayType(EnvironmentSortCriteria)),
        gql.Argument('pageSize', gql.Integer),
    ],
)


EnvironmentDataItemFilter = gql.InputType(
    name='EnvironmentDataItemFilter',
    arguments=[
        gql.Argument('itemTypes', gql.ArrayType(gql.String)),
        gql.Argument('term', gql.String),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
    ],
)


InviteGroupOnEnvironmentInput = gql.InputType(
    name='InviteGroupOnEnvironmentInput',
    arguments=[
        gql.Argument('permissions', gql.ArrayType(gql.String)),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('groupUri', gql.NonNullableType(gql.String)),
        gql.Argument('environmentIAMRoleName', gql.String),
    ],
)

AddConsumptionRoleToEnvironmentInput = gql.InputType(
    name='AddConsumptionRoleToEnvironmentInput',
    arguments=[
        gql.Argument('consumptionRoleName', gql.NonNullableType(gql.String)),
        gql.Argument('groupUri', gql.NonNullableType(gql.String)),
        gql.Argument('IAMRoleArn', gql.NonNullableType(gql.String)),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
    ],
)

ConsumptionRoleFilter = gql.InputType(
    name='ConsumptionRoleFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
        gql.Argument('groupUri', gql.NonNullableType(gql.String)),
    ],
)
