"""Defines the object types of the SageMaker notebooks"""

from dataall.base.api import gql
from dataall.modules.notebooks.api.resolvers import (
    resolve_notebook_stack,
    resolve_notebook_status,
    resolve_user_role,
)

from dataall.core.environment.api.resolvers import resolve_environment
from dataall.core.organizations.api.resolvers import resolve_organization_by_env

from dataall.modules.notebooks.api.enums import SagemakerNotebookRole


Maintenance = gql.ObjectType(
    name='Maintenance',
    fields=[
        gql.Field(name='status', type=gql.String),
        gql.Field(name='mode', type=gql.String)
    ]
)
