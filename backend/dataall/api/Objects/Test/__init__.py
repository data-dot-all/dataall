from datetime import datetime

from ... import gql

TestType = gql.ObjectType(
    name="TestType",
    fields=[
        gql.Field(name="_ts", type=gql.String),
        gql.Field(name="message", type=gql.String),
        gql.Field(name="arg", type=gql.String),
        gql.Field(name="username", type=gql.String),
        gql.Field(name="groups", type=gql.ArrayType(gql.String)),
    ],
)


def test_resolver(context, source, arg: str = None):
    return {
        "_ts": datetime.now().isoformat(),
        "message": "server is up",
        "username": context.username,
        "groups": context.groups or [],
        "arg": arg or "",
    }


test_field = gql.QueryField(
    name="up",
    args=[gql.Argument(name="arg", type=gql.String)],
    type=TestType,
    resolver=test_resolver,
)
