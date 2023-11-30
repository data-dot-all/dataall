"""The module defines GraphQL queries for the SageMaker ML Studio"""
from dataall.base.api import gql
from dataall.modules.mlstudio.api.resolvers import (
    get_sagemaker_studio_user,
    list_sagemaker_studio_users,
    get_sagemaker_studio_user_presigned_url,
    list_environment_sagemaker_studio_domains
)

getSagemakerStudioUser = gql.QueryField(
    name='getSagemakerStudioUser',
    args=[
        gql.Argument(
            name='sagemakerStudioUserUri', type=gql.NonNullableType(gql.String)
        )
    ],
    type=gql.Ref('SagemakerStudioUser'),
    resolver=get_sagemaker_studio_user,
)

listSagemakerStudioUsers = gql.QueryField(
    name='listSagemakerStudioUsers',
    args=[gql.Argument('filter', gql.Ref('SagemakerStudioUserFilter'))],
    type=gql.Ref('SagemakerStudioUserSearchResult'),
    resolver=list_sagemaker_studio_users,
)

getSagemakerStudioUserPresignedUrl = gql.QueryField(
    name='getSagemakerStudioUserPresignedUrl',
    args=[
        gql.Argument(
            name='sagemakerStudioUserUri', type=gql.NonNullableType(gql.String)
        )
    ],
    type=gql.String,
    resolver=get_sagemaker_studio_user_presigned_url,
)

listEnvironmentMLStudioDomains = gql.QueryField(
    name='listEnvironmentMLStudioDomains',
    args=[
        gql.Argument('filter', gql.Ref('SagemakerStudioDomainFilter')),
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Ref('SagemakerStudioDomainSearchResult'),
    resolver=list_environment_sagemaker_studio_domains,
)
