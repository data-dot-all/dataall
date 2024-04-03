"""The module defines GraphQL mutations for the SageMaker notebooks"""

from dataall.base.api import gql
from dataall.modules.notebooks.api.resolvers import (
    create_notebook,
    delete_notebook,
    start_notebook,
    stop_notebook,
)

createSagemakerNotebook = gql.MutationField(
    name='createSagemakerNotebook',
    args=[gql.Argument(name='input', type=gql.Ref('NewSagemakerNotebookInput'))],
    type=gql.Ref('SagemakerNotebook'),
    resolver=create_notebook,
)

startSagemakerNotebook = gql.MutationField(
    name='startSagemakerNotebook',
    args=[gql.Argument(name='notebookUri', type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=start_notebook,
)

stopSagemakerNotebook = gql.MutationField(
    name='stopSagemakerNotebook',
    args=[gql.Argument(name='notebookUri', type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=stop_notebook,
)

deleteSagemakerNotebook = gql.MutationField(
    name='deleteSagemakerNotebook',
    args=[
        gql.Argument(name='notebookUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='deleteFromAWS', type=gql.Boolean),
    ],
    type=gql.String,
    resolver=delete_notebook,
)
