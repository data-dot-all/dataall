from ... import gql
from .resolvers import *


listTenantPermissions = gql.QueryField(
    name='listTenantPermissions',
    type=gql.ArrayType(gql.Ref('Permission')),
    resolver=list_tenant_permissions,
)

listTenantGroups = gql.QueryField(
    name='listTenantGroups',
    args=[
        gql.Argument(name='filter', type=gql.Ref('GroupFilter')),
    ],
    type=gql.Ref('GroupSearchResult'),
    resolver=list_tenant_groups,
)

getMonitoringDashboardId = gql.QueryField(
    name='getMonitoringDashboardId',
    type=gql.String,
    resolver=get_monitoring_dashboard_id,
)

getMonitoringVpcConnectionId = gql.QueryField(
    name='getMonitoringVPCConnectionId',
    type=gql.String,
    resolver=get_monitoring_vpc_connection_id,
)

getPlatformAuthorSession = gql.QueryField(
    name='getPlatformAuthorSession',
    args=[
        gql.Argument(name='awsAccount', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.String,
    resolver=get_quicksight_author_session,
)

getPlatformReaderSession = gql.QueryField(
    name='getPlatformReaderSession',
    args=[
        gql.Argument(name='dashboardId', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.String,
    resolver=get_quicksight_reader_session,
)
