from ... import gql
from .resolvers import *
from ....api.constants import RedshiftClusterRole

RedshiftCluster = gql.ObjectType(
    name='RedshiftCluster',
    fields=[
        gql.Field(name='clusterUri', type=gql.ID),
        gql.Field(name='environmentUri', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='clusterArn', type=gql.String),
        gql.Field(name='clusterName', type=gql.String),
        gql.Field(name='databaseName', type=gql.String),
        gql.Field(name='databaseUser', type=gql.String),
        gql.Field(name='datahubSecret', type=gql.String),
        gql.Field(name='masterUsername', type=gql.String),
        gql.Field(name='masterDatabaseName', type=gql.String),
        gql.Field(name='masterSecret', type=gql.String),
        gql.Field(name='nodeType', type=gql.String),
        gql.Field(name='numberOfNodes', type=gql.Integer),
        gql.Field(name='kmsAlias', type=gql.String),
        gql.Field(name='subnetGroupName', type=gql.String),
        gql.Field(name='CFNStackName', type=gql.String),
        gql.Field(name='CFNStackStatus', type=gql.String),
        gql.Field(name='CFNStackArn', type=gql.String),
        gql.Field(name='port', type=gql.String),
        gql.Field(name='endpoint', type=gql.String),
        gql.Field(name='SamlGroupName', type=gql.String),
        gql.Field(name='imported', type=gql.Boolean),
        gql.Field(name='IAMRoles', type=gql.ArrayType(gql.String)),
        gql.Field(name='vpc', type=gql.String),
        gql.Field(name='subnetIds', type=gql.ArrayType(gql.String)),
        gql.Field(name='securityGroupIds', type=gql.ArrayType(gql.String)),
        gql.Field(
            name='userRoleForCluster',
            type=RedshiftClusterRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
        gql.Field(
            name='userRoleInEnvironment', type=RedshiftClusterRole.toGraphQLEnum()
        ),
        gql.Field(
            'organization',
            type=gql.Ref('Organization'),
            resolver=get_cluster_organization,
        ),
        gql.Field(
            'environment', type=gql.Ref('Environment'), resolver=get_cluster_environment
        ),
        gql.Field('status', type=gql.String, resolver=get_cluster_status),
        gql.Field(name='stack', type=gql.Ref('Stack'), resolver=resolve_stack),
    ],
)


RedshiftClusterSearchResult = gql.ObjectType(
    name='RedshiftClusterSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(RedshiftCluster)),
    ],
)

RedshiftClusterFilter = gql.InputType(
    name='RedshiftClusterFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('roles', gql.ArrayType(gql.Ref('RedshiftClusterRole'))),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)

RedshiftClusterCredentials = gql.ObjectType(
    name='RedshiftClusterCredentials',
    fields=[
        gql.Field(name='clusterUri', type=gql.ID),
        gql.Field('endpoint', gql.String),
        gql.Field('database', gql.String),
        gql.Field('port', gql.Integer),
        gql.Field('password', gql.String),
        gql.Field('user', gql.String),
    ],
)
