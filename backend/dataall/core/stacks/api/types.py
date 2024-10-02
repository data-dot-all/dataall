from dataall.base.api import gql
from dataall.core.stacks.api.resolvers import (
    resolve_link,
    resolve_resources,
    resolve_outputs,
    resolve_events,
    resolve_task_id,
    resolve_error,
    resolve_stack_visibility,
)

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
        gql.Field(name='updated', type=gql.AWSDateTime),
        gql.Field(name='link', type=gql.String, resolver=resolve_link),
        gql.Field(name='outputs', type=gql.String, resolver=resolve_outputs),
        gql.Field(name='resources', type=gql.String, resolver=resolve_resources),
        gql.Field(name='error', type=gql.String, resolver=resolve_error),
        gql.Field(name='events', type=gql.String, resolver=resolve_events),
        gql.Field(name='EcsTaskArn', type=gql.String),
        gql.Field(name='EcsTaskId', type=gql.String, resolver=resolve_task_id),
        gql.Field(name='canViewLogs', type=gql.Boolean, resolver=resolve_stack_visibility),
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


KeyValueTag = gql.ObjectType(
    name='KeyValueTag',
    fields=[
        gql.Field(name='tagUri', type=gql.ID),
        gql.Field(name='targetType', type=gql.String),
        gql.Field(name='targetUri', type=gql.String),
        gql.Field(name='key', type=gql.String),
        gql.Field(name='value', type=gql.String),
        gql.Field(name='cascade', type=gql.Boolean),
    ],
)
