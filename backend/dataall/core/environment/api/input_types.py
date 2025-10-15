from dataall.base.api import gql
from dataall.base.api.constants import GraphQLEnumMapper, SortDirection
from dataall.core.environment.db.environment_enums import PolicyManagementOptions

AwsEnvironmentInput = gql.InputType(
    name='AwsEnvironmentInput',
    arguments=[
        gql.Argument('AwsAccountId', gql.NonNullableType(gql.String)),
        gql.Argument('region', gql.NonNullableType(gql.String)),
    ],
)

ModifyEnvironmentParameterInput = gql.InputType(
    name='ModifyEnvironmentParameterInput',
    arguments=[gql.Argument('key', gql.String), gql.Argument('value', gql.String)],
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
        gql.Argument('EnvironmentDefaultIAMRoleArn', gql.String),
        gql.Argument('resourcePrefix', gql.String),
        gql.Argument('parameters', gql.ArrayType(ModifyEnvironmentParameterInput)),
        gql.Argument('vpcId', gql.String),
        gql.Argument('subnetIds', gql.ArrayType(gql.String)),
        gql.Argument('type', gql.String),
    ],
)

ModifyEnvironmentInput = gql.InputType(
    name='ModifyEnvironmentInput',
    arguments=[
        gql.Argument('label', gql.String),
        gql.Argument('description', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('SamlGroupName', gql.String),
        gql.Argument('resourcePrefix', gql.String),
        gql.Argument('parameters', gql.ArrayType(ModifyEnvironmentParameterInput)),
        gql.Argument('vpcId', gql.String),
        gql.Argument('subnetIds', gql.ArrayType(gql.String)),
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
        gql.Argument(name='field', type=gql.NonNullableType(EnvironmentSortField.toGraphQLEnum())),
        gql.Argument(name='direction', type=gql.NonNullableType(SortDirection.toGraphQLEnum())),
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
        gql.Argument('SamlGroupName', gql.String),
        gql.Argument('sort', gql.ArrayType(EnvironmentSortCriteria)),
        gql.Argument('pageSize', gql.Integer),
    ],
)


InviteGroupOnEnvironmentInput = gql.InputType(
    name='InviteGroupOnEnvironmentInput',
    arguments=[
        gql.Argument('permissions', gql.ArrayType(gql.String)),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('groupUri', gql.NonNullableType(gql.String)),
        gql.Argument('environmentIAMRoleArn', gql.String),
    ],
)

AddConsumptionPrincipalToEnvironmentInput = gql.InputType(
    name='AddConsumptionPrincipalToEnvironmentInput',
    arguments=[
        gql.Argument('consumptionPrincipalName', gql.NonNullableType(gql.String)),
        gql.Argument('groupUri', gql.NonNullableType(gql.String)),
        gql.Argument('IAMPrincipalArn', gql.NonNullableType(gql.String)),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('dataallManaged', gql.NonNullableType(PolicyManagementOptions.toGraphQLEnum())),
    ],
)

ConsumptionPrincipalFilter = gql.InputType(
    name='ConsumptionPrincipalFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
        gql.Argument(name='groupUri', type=gql.String),
    ],
)

UpdateConsumptionPrincipalInput = gql.InputType(
    name='UpdateConsumptionPrincipalInput',
    arguments=[
        gql.Argument('consumptionPrincipalName', gql.String),
        gql.Argument('groupUri', gql.String),
        gql.Argument('dataallManaged', gql.NonNullableType(PolicyManagementOptions.toGraphQLEnum())),
    ],
)
