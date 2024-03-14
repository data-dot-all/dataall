from enum import Enum

import pytest
import dataall.base.api.gql as gql


@pytest.fixture(scope='module')
def episode():
    class EpisodeEnum(Enum):
        NEWHOPE = 'CANCELLED'
        EMPIRE = 'FAILED'
        JEDI = 'QUEUED'

    yield gql.Enum(name='Episode', values=EpisodeEnum)


def test_enum_definition(episode):
    expected = """enum Episode{
NEWHOPE
EMPIRE
JEDI
}"""
    assert episode.gql() == expected


def test_enum_as_field(episode):
    f = gql.Field(name='foo', type=episode)
    assert f.gql() == 'foo : Episode'


def test_enum_as_arg(episode):
    arg = gql.Argument(name='foo', type=episode)
    assert arg.gql() == 'foo : Episode'


def test_enum_as_list(episode):
    l = gql.ArrayType(episode)
    assert l.gql() == '[Episode]'


def test_enum_as_non_nullable(episode):
    l = gql.NonNullableType(episode)
    assert l.gql() == 'Episode!'


def test_enum_in_input_type(episode):
    i = gql.InputType(
        name='foo',
        arguments=[
            gql.Argument(name='episode', type=episode),
            gql.Argument(name='x', type=gql.NonNullableType(gql.ArrayType(gql.String))),
        ],
    )
    assert i.gql() == 'input foo{  episode : Episode, x : [String]! }'


def test_schema_with_enums(episode):
    s = gql.Schema(
        types=[
            gql.ObjectType(
                name='user',
                fields=[
                    gql.Field(name='name', type=gql.String),
                    gql.Field(name='role', type=gql.Ref('Episode')),
                ],
            )
        ],
        enums=[episode],
    )

    print(s.gql())
