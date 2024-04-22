from dataall.base.api import gql


def test_cached_types():
    foo = gql.ObjectType(name='foo', fields=[gql.Field(name='id', type=gql.ID)])

    bar = gql.ObjectType(name='bar', fields=[gql.Field(name='id', type=gql.ID)])

    assert len(gql.ObjectType.class_instances.get('default', {}).keys()) == 2
    assert gql.ObjectType.get_instance('foo') is not None
    assert gql.ObjectType.get_instance('foo').name == 'foo'
    assert gql.ObjectType.get_instance('bar') is not None
    assert gql.ObjectType.get_instance('bar').name == 'bar'


def test_cached_query_fields():
    foo = gql.QueryField(name='foo', type=gql.String)

    bar = gql.QueryField(name='bar', type=gql.String)

    assert len(gql.QueryField.class_instances.get('default', {}).keys()) == 2
    assert gql.QueryField.get_instance('foo') is not None
    assert gql.QueryField.get_instance('foo').name == 'foo'
    assert gql.QueryField.get_instance('bar') is not None
    assert gql.QueryField.get_instance('bar').name == 'bar'
