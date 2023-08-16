import dataall.base.api.gql as gql


def test_non_nullable_modifier_scalar():
    assert gql.NonNullableType(gql.String).gql() == 'String!'


def test_non_nullable_modifier_thunk():
    Bar = gql.Field(name='Bar', type=gql.String)
    assert gql.NonNullableType(gql.Thunk(lambda: Bar)).gql() == 'Bar!'


def test_non_nullable_modifier_thunk():
    Bar = gql.Field(name='Bar', type=gql.String)
    condition = gql.NonNullableType(gql.Thunk(lambda: Bar)).gql() == 'Bar!'
    assert condition


def test_array_modifier_thunk():
    Bar = gql.Field(name='Bar', type=gql.String)
    condition = gql.ArrayType(gql.Thunk(lambda: Bar)).gql() == '[Bar]'
    assert condition


def test_nesting():
    Bar = gql.Field(name='Bar', type=gql.String)
    assert gql.ArrayType(gql.NonNullableType(gql.Thunk(lambda: Bar))).gql() == '[Bar!]'


def test_strip():
    Foo = gql.ObjectType(name='Foo', fields='Foo', directives=[])
    field = gql.Field(type=Foo, name='foo')

    # list of NamedTypes


"""
directives - less relations
Relation One To One
One  To Many
type Foo{
    bars:[Bar]
}

type Bar{
    foo : Foo
}

One To One
type Foo {
    bar : Bar
}

type Bar{
    foo : Foo
}

OneToMany :
type Foo{
    bars:[Bar]
}


type Bar{
    foos:[Foo]
}

"""
