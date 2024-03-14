import dataall.base.api.gql as gql


def test_base_object():
    Point = gql.ObjectType(
        name='Point',
        fields=[
            gql.Field(name='x', type=gql.String),
            gql.Field(name='y', type=gql.String),
        ],
    )

    Shape = gql.ObjectType(name='Shape', fields=[gql.Field(name='point', type=gql.ArrayType(Point))])
    assert 'type Point' in Point.gql()
    assert 'x : String' in Point.gql()
    assert 'y : String' in Point.gql()
    assert 'type Shape' in Shape.gql()
    assert 'point : [Point]' in Shape.gql()


def test_object_type_with_directive():
    Point = gql.ObjectType(
        name='Point',
        fields=[
            gql.Field(name='x', type=gql.String),
            gql.Field(name='y', type=gql.String),
        ],
        directives=[gql.DirectiveArgs(name='model')],
    )

    print(Point.gql())
    assert 'type Point' in Point.gql()
    assert 'x : String' in Point.gql()
    assert 'y : String' in Point.gql()
    assert Point.directive('model').name == 'model'
