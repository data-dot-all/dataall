from backend.api import gql
from backend.api.Module.resolvers import *

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
