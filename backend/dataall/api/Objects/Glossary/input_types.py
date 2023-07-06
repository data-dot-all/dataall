from dataall.base.api import gql

CreateGlossaryInput = gql.InputType(
    name='CreateGlossaryInput',
    arguments=[
        gql.Argument(name='label', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='readme', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='status', type=gql.String),
        gql.Argument(name='admin', type=gql.String),
    ],
)

UpdateGlossaryInput = gql.InputType(
    name='UpdateGlossaryInput',
    arguments=[
        gql.Argument(name='label', type=gql.String),
        gql.Argument(name='readme', type=gql.String),
        gql.Argument(name='status', type=gql.String),
        gql.Argument(name='admin', type=gql.String),
    ],
)


CreateCategoryInput = gql.InputType(
    name='CreateCategoryInput',
    arguments=[
        gql.Argument(name='label', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='readme', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='status', type=gql.String),
    ],
)

UpdateCategoryInput = gql.InputType(
    name='UpdateCategoryInput',
    arguments=[
        gql.Argument(name='label', type=gql.String),
        gql.Argument(name='readme', type=gql.String),
        gql.Argument(name='status', type=gql.String),
    ],
)

CreateTermInput = gql.InputType(
    name='CreateTermInput',
    arguments=[
        gql.Argument(name='label', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='readme', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='status', type=gql.String),
    ],
)


UpdateTermInput = gql.InputType(
    name='UpdateTermInput',
    arguments=[
        gql.Argument(name='label', type=gql.String),
        gql.Argument(name='readme', type=gql.String),
        gql.Argument(name='status', type=gql.String),
    ],
)


GlossaryFilter = gql.InputType(
    name='GlossaryFilter',
    arguments=[
        gql.Argument(name='term', type=gql.String),
        gql.Argument(name='status', type=gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)

CategoryFilter = gql.InputType(
    name='CategoryFilter',
    arguments=[
        gql.Argument(name='term', type=gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='status', type=gql.String),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)


TermFilter = gql.InputType(
    name='TermFilter',
    arguments=[
        gql.Argument(name='status', type=gql.String),
        gql.Argument(name='term', type=gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)

GlossaryTermTargetFilter = gql.InputType(
    name='GlossaryTermTargetFilter',
    arguments=[
        gql.Argument(name='term', type=gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)

GlossaryNodeSearchFilter = gql.InputType(
    name='GlossaryNodeSearchFilter',
    arguments=[
        gql.Argument(name='term', type=gql.String),
        gql.Argument(name='nodeType', type=gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)
