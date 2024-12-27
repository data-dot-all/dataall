from dataall.base.api import gql
from dataall.modules.dashboards.api.resolvers import (
    DashboardRole,
    get_dashboard_restricted_information,
    resolve_glossary_terms,
    resolve_upvotes,
    resolve_user_role,
)

from dataall.core.environment.api.resolvers import resolve_environment

DashboardRestrictedInformation = gql.ObjectType(
    name='DashboardRestrictedInformation',
    fields=[gql.Field('AwsAccountId', type=gql.String), gql.Field('region', type=gql.String)],
)

Dashboard = gql.ObjectType(
    name='Dashboard',
    fields=[
        gql.Field('dashboardUri', type=gql.ID),
        gql.Field('name', type=gql.String),
        gql.Field('label', type=gql.String),
        gql.Field('description', type=gql.String),
        gql.Field('DashboardId', type=gql.String),
        gql.Field('tags', type=gql.ArrayType(gql.String)),
        gql.Field('created', type=gql.String),
        gql.Field('updated', type=gql.String),
        gql.Field('owner', type=gql.String),
        gql.Field('SamlGroupName', type=gql.String),
        gql.Field(
            'restricted',
            type=DashboardRestrictedInformation,
            resolver=get_dashboard_restricted_information,
        ),
        gql.Field(
            'environment',
            type=gql.Ref('EnvironmentSimplified'),
            resolver=resolve_environment,
        ),
        gql.Field(
            'userRoleForDashboard',
            type=DashboardRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
        gql.Field(
            name='terms',
            type=gql.Ref('TermSearchResult'),
            resolver=resolve_glossary_terms,
        ),
        gql.Field(
            'upvotes',
            type=gql.Integer,
            resolver=resolve_upvotes,
        ),
    ],
)

DashboardShare = gql.ObjectType(
    name='DashboardShare',
    fields=[
        gql.Field('shareUri', type=gql.ID),
        gql.Field('dashboardUri', type=gql.ID),
        gql.Field('name', type=gql.String),
        gql.Field('label', type=gql.String),
        gql.Field('SamlGroupName', type=gql.String),
        gql.Field('status', type=gql.String),
        gql.Field('owner', type=gql.String),
        gql.Field('tags', type=gql.ArrayType(gql.String)),
        gql.Field('created', type=gql.String),
        gql.Field('updated', type=gql.String),
    ],
)

DashboardSearchResults = gql.ObjectType(
    name='DashboardSearchResults',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(Dashboard)),
    ],
)

DashboardShareSearchResults = gql.ObjectType(
    name='DashboardShareSearchResults',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(DashboardShare)),
    ],
)
