import dataall.base.api.gql as gql


def test_base_field():
    bar = gql.Field(name='bar', type=gql.String)
    assert bar.gql() == 'bar : String'


def test_modifier_type():
    bar = gql.Field(name='bar', type=gql.NonNullableType(gql.String))
    assert bar.gql() == 'bar : String!'


def test_object_ref():
    Point = gql.ObjectType(name='Point', fields=[gql.Field(name='x', type=gql.Number)])

    ref = gql.Field(name='point', type=Point)
    assert ref.gql() == 'point : Point'

    ref = gql.Field(name='point', type=gql.ArrayType(Point))
    assert ref.gql() == 'point : [Point]'

    ref = gql.Field(name='point', type=gql.NonNullableType(Point))
    assert ref.gql() == 'point : Point!'


def test_field_directives():
    f = gql.Field(
        name='foo',
        type=gql.String,
        directives=[gql.DirectiveArgs(name='hasmany', child=['x'])],
    )
    assert f.gql() == "foo : String @hasmany(child:['x'])"
    assert f.directive('hasmany').name == 'hasmany'
    assert f.directive('hasmany').args['child'][0] == 'x'

    assert f.has_directive('hasmany')

    assert f.has_directive('foo') is False


def test_resolver():
    def getMeFoo(context=None, source=None, **data):
        return {'id': data['id']}

    Foo = gql.ObjectType(name='Foo', fields=[gql.Field(name='id', type=gql.String)])
    Query = gql.ObjectType(name='Query', fields=[gql.Field(name='getMeFoo', type=Foo, resolver=getMeFoo)])
    schema = gql.Schema(types=[Foo, Query])

    result = schema.resolve(context=None, path='Query/getMeFoo', source=None, id='1')
    assert result['id'] == '1'


def test_is_array_of():
    Foo = gql.ObjectType(name='Foo', fields=[gql.Field(name='id', type=gql.String)])
    field = gql.Field(name='field', type=Foo)
    assert not field.is_array

    field = gql.Field(name='field', type=gql.ArrayType(Foo))
    assert field.is_array

    field = gql.Field(name='field', type=gql.ArrayType(gql.NonNullableType(Foo)))
    assert field.is_array

    field = gql.Field(name='field', type=gql.NonNullableType(gql.ArrayType(Foo)))
    assert field.is_array
