from ... import gql
from .resolvers import *

createSagemakerStudioUserProfile = gql.MutationField(
    name='createSagemakerStudioUserProfile',
    args=[
        gql.Argument(
            name='input',
            type=gql.NonNullableType(gql.Ref('NewSagemakerStudioUserProfileInput')),
        )
    ],
    type=gql.Ref('SagemakerStudioUserProfile'),
    resolver=create_sagemaker_studio_user_profile,
)

deleteSagemakerStudioUserProfile = gql.MutationField(
    name='deleteSagemakerStudioUserProfile',
    args=[
        gql.Argument(
            name='sagemakerStudioUserProfileUri',
            type=gql.NonNullableType(gql.String),
        ),
        gql.Argument(name='deleteFromAWS', type=gql.Boolean),
    ],
    type=gql.String,
    resolver=delete_sagemaker_studio_user_profile,
)
