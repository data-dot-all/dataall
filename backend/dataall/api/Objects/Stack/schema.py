from dataall import gql
from .resolvers import *

Stack = gql.ObjectType(
    name='Stack',
    fields=[
        gql.Field(name='stackUri', type=gql.ID),
        gql.Field(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='stack', type=gql.NonNullableType(gql.String)),
        gql.Field(name='environmentUri', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='accountid', type=gql.NonNullableType(gql.String)),
        gql.Field(name='region', type=gql.NonNullableType(gql.String)),
        gql.Field(name='status', type=gql.String),
        gql.Field(name='stackid', type=gql.String),
        gql.Field(name='link', type=gql.String, resolver=resolve_link),
        gql.Field(name='outputs', type=gql.String, resolver=resolve_outputs),
        gql.Field(name='resources', type=gql.String, resolver=resolve_resources),
        gql.Field(name='error', type=gql.String, resolver=resolve_error),
        gql.Field(name='events', type=gql.String, resolver=resolve_events),
        gql.Field(name='EcsTaskArn', type=gql.String),
        gql.Field(name='EcsTaskId', type=gql.String, resolver=resolve_task_id),
    ],
)

StackLog = gql.ObjectType(
    name='StackLog',
    fields=[
        gql.Field(name='logStream', type=gql.String),
        gql.Field(name='logGroup', type=gql.String),
        gql.Field(name='timestamp', type=gql.String),
        gql.Field(name='message', type=gql.String),
    ],
)
