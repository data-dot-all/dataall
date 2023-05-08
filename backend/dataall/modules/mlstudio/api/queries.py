"""The module defines GraphQL queries for the SageMaker ML Studio"""
from dataall.api import gql
from dataall.modules.mlstudio.api.resolvers import (
    get_sagemaker_studio_user_profile,
    get_user_profile_applications,
    list_sm_studio_user_profile,
    get_sagemaker_studio_user_profile_presigned_url,
)

getSagemakerStudioUserProfile = gql.QueryField(
    name='getSagemakerStudioUserProfile',
    args=[
        gql.Argument(
            name='sagemakerStudioUserProfileUri', type=gql.NonNullableType(gql.String)
        )
    ],
    type=gql.Ref('SagemakerStudioUserProfile'),
    resolver=get_sagemaker_studio_user_profile,
)

getSagemakerStudioUserProfileApps = gql.QueryField(
    name='getSagemakerStudioUserProfileApps',
    args=[
        gql.Argument(
            name='sagemakerStudioUserProfileUri', type=gql.NonNullableType(gql.String)
        )
    ],
    type=gql.ArrayType(gql.Ref('SagemakerStudioUserProfileApps')),
    resolver=get_user_profile_applications,
)

listSagemakerStudioUserProfiles = gql.QueryField(
    name='listSagemakerStudioUserProfiles',
    args=[gql.Argument('filter', gql.Ref('SagemakerStudioUserProfileFilter'))],
    type=gql.Ref('SagemakerStudioUserProfileSearchResult'),
    resolver=list_sm_studio_user_profile,
)

getSagemakerStudioUserProfilePresignedUrl = gql.QueryField(
    name='getSagemakerStudioUserProfilePresignedUrl',
    args=[
        gql.Argument(
            name='sagemakerStudioUserProfileUri', type=gql.NonNullableType(gql.String)
        )
    ],
    type=gql.String,
    resolver=get_sagemaker_studio_user_profile_presigned_url,
)
