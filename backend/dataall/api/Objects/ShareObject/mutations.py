from .resolvers import *

createShareObject = gql.MutationField(
    name='createShareObject',
    args=[
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='itemUri', type=gql.String),
        gql.Argument(name='itemType', type=gql.String),
        gql.Argument(
            name='input', type=gql.NonNullableType(gql.Ref('NewShareObjectInput'))
        ),
    ],
    type=gql.Ref('ShareObject'),
    resolver=create_share_object,
)

deleteShareObject = gql.MutationField(
    name='deleteShareObject',
    args=[gql.Argument(name='shareUri', type=gql.NonNullableType(gql.String))],
    resolver=delete_share_object,
    type=gql.Boolean
)

addSharedItem = gql.MutationField(
    name='addSharedItem',
    args=[
        gql.Argument(name='shareUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=gql.Ref('AddSharedItemInput')),
    ],
    type=gql.Ref('ShareItem'),
    resolver=add_shared_item,
)


removeSharedItem = gql.MutationField(
    name='removeSharedItem',
    args=[gql.Argument(name='shareItemUri', type=gql.NonNullableType(gql.String))],
    resolver=remove_shared_item,
    type=gql.Boolean,
)

submitShareObject = gql.MutationField(
    name='submitShareObject',
    args=[gql.Argument(name='shareUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('ShareObject'),
    resolver=submit_share_object,
)

approveShareObject = gql.MutationField(
    name='approveShareObject',
    args=[gql.Argument(name='shareUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('ShareObject'),
    resolver=approve_share_object,
)


rejectShareObject = gql.MutationField(
    name='rejectShareObject',
    args=[gql.Argument(name='shareUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('ShareObject'),
    resolver=reject_share_object,
)

revokeItemsShareObject = gql.MutationField(
    name='revokeItemsShareObject',
    args=[gql.Argument(name='input', type=gql.Ref('RevokeItemsInput'))],
    type=gql.Ref('ShareObject'),
    resolver=revoke_items_share_object,
)
