import dataall.base.api.gql as gql


def test_base():
    arg = gql.Argument(name='foo', type=gql.String)
    assert arg.gql() == 'foo : String'

    arg = gql.Argument(name='foo', type=gql.Integer)
    assert arg.gql() == 'foo : Int'

    arg = gql.Argument(name='foo', type=gql.NonNullableType(gql.String))
    assert arg.gql() == 'foo : String!'

    arg = gql.Argument(name='foo', type=gql.ArrayType(gql.String))
    assert arg.gql() == 'foo : [String]'

    arg = gql.Argument(name='foo', type=gql.NonNullableType(gql.ArrayType(gql.String)))
    assert arg.gql() == 'foo : [String]!'

    arg = gql.Argument(name='foo', type=gql.Thunk(lambda: gql.String))
    assert arg.gql() == 'foo : String'

    arg = gql.Argument(name='foo', type=gql.Thunk(lambda: gql.NonNullableType(gql.String)))
    assert arg.gql() == 'foo : String!'

    arg = gql.Argument(name='foo', type=gql.Thunk(lambda: gql.ArrayType(gql.String)))
    assert arg.gql() == 'foo : [String]'


def test_invalid_entry():
    Foo = gql.ObjectType(name='Foo', fields=[gql.Field(name='id', type=gql.String)])
    try:
        gql.Argument(name='foo', type=Foo)
        assert False
    except Exception:
        assert True

    try:
        gql.Argument(name='foo', type=gql.NonNullableType(Foo))
        assert False
    except Exception:
        assert True

    try:
        gql.Argument(name='foo', type=gql.ArrayType(Foo))
        assert False
    except Exception:
        assert True

    try:
        gql.Argument(name='foo', type=gql.Thunk(lambda: Foo))
        assert False
    except Exception:
        assert True


def test_arg_from_input_type():
    point_input = gql.InputType(
        name='PointInput',
        arguments=[
            gql.Argument(name='x', type=gql.Integer),
            gql.Argument(name='y', type=gql.Integer),
        ],
    )
    point_arg = gql.Argument(name='point', type=point_input)

    assert point_arg.gql() == 'point : PointInput'

    point_args = gql.Argument(name='points', type=gql.ArrayType(point_input))

    print('**~~%%' * 30)
    assert point_args.gql() == 'points : [PointInput]'


def test_input_type_with_arg():
    input_type = gql.InputType(
        name='NewPointInputType',
        arguments=[
            gql.Argument(name='x', type=gql.Integer),
            gql.Argument(name='y', type=gql.Integer),
        ],
    )
    assert input_type.gql() == 'input NewPointInputType{  x : Int, y : Int }'


def test_nested_input():
    point_input_type = gql.InputType(
        name='NewPointInputType',
        arguments=[
            gql.Argument(name='x', type=gql.Integer),
            gql.Argument(name='y', type=gql.Integer),
        ],
    )

    shape_input_type = gql.InputType(
        name='NewShapeInputType',
        arguments=[gql.Argument(name='points', type=point_input_type)],
    )
    print(shape_input_type.gql())

    assert shape_input_type.gql() == 'input NewShapeInputType{  points : NewPointInputType }'

    square_input_type = gql.InputType(
        name='NewSquare',
        arguments=[
            gql.Argument(name='topleft', type=point_input_type),
            gql.Argument(name='topright', type=point_input_type),
            gql.Argument(name='bottomleft', type=point_input_type),
            gql.Argument(name='bottomright', type=point_input_type),
        ],
    )

    print(square_input_type.gql())
