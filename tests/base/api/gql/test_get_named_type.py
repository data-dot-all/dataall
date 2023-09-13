import dataall.base.api.gql as gql


def test_scalar():
    assert gql.get_named_type(gql.String) == gql.String
    assert gql.get_named_type(gql.Number) == gql.Number
    assert gql.get_named_type(gql.Date) == gql.Date
    assert gql.get_named_type(gql.Boolean) == gql.Boolean


def test_modified_type():
    assert gql.get_named_type(gql.ArrayType(gql.String)) == gql.String
    assert gql.get_named_type(gql.NonNullableType(gql.String)) == gql.String


def test_object_type():
    foo = gql.ObjectType(name='foo', fields=[])
    assert gql.get_named_type(foo) == foo


def test_object_type_modifiers():
    foo = gql.ObjectType(name='foo', fields=[])
    assert gql.get_named_type(gql.NonNullableType(foo)) == foo
    assert gql.get_named_type(gql.ArrayType(foo)) == foo


def test_thunk():
    foo = gql.ObjectType(name='foo', fields=[])
    assert gql.get_named_type(gql.Thunk(lambda: foo)) == foo


def test_modifier_thunk():
    foo = gql.ObjectType(name='foo', fields=[])
    assert gql.get_named_type(gql.ArrayType(gql.Thunk(lambda: foo))) == foo
    assert gql.get_named_type(gql.NonNullableType(gql.Thunk(lambda: foo))) == foo


def test_thunk_modifier():
    foo = gql.ObjectType(name='foo', fields=[])
    assert gql.get_named_type(gql.Thunk(lambda: gql.ArrayType(foo))) == foo
