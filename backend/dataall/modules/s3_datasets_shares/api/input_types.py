from dataall.base.api.constants import gql


ModifyFiltersTableShareItemInput = gql.InputType(
    name='ModifyFiltersTableShareItemInput',
    arguments=[
        gql.Argument(name='shareItemUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filterUris', type=gql.ArrayType(gql.String)),
    ],
)
