"""The module defines GraphQL queries for the SageMaker notebooks"""

from dataall.base.api import gql
from dataall.modules.notebooks.api.resolvers import get_notebook, list_notebooks, get_notebook_presigned_url

getSagemakerNotebook = gql.QueryField(
    name='getSagemakerNotebook',
    args=[gql.Argument(name='notebookUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('SagemakerNotebook'),
    resolver=get_notebook,
)

listSagemakerNotebooks = gql.QueryField(
    name='listSagemakerNotebooks',
    args=[gql.Argument('filter', gql.Ref('SagemakerNotebookFilter'))],
    type=gql.Ref('SagemakerNotebookSearchResult'),
    resolver=list_notebooks,
)

getSagemakerNotebookPresignedUrl = gql.QueryField(
    name='getSagemakerNotebookPresignedUrl',
    args=[gql.Argument(name='notebookUri', type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=get_notebook_presigned_url,
)
