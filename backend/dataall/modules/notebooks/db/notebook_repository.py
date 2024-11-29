"""
DAO layer that encapsulates the logic and interaction with the database for notebooks
Provides the API to retrieve / update / delete notebooks
"""

from sqlalchemy import or_
from sqlalchemy.sql import and_
from sqlalchemy.orm import Query

from dataall.base.db import paginate
from dataall.modules.notebooks.db.notebook_models import SagemakerNotebook
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)


class NotebookRepository(EnvironmentResource):
    """DAO layer for notebooks"""

    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 10

    def __init__(self, session):
        self._session = session

    def save_notebook(self, notebook):
        """Save notebook to the database"""
        self._session.add(notebook)
        self._session.commit()

    def find_notebook(self, uri) -> SagemakerNotebook:
        """Finds a notebook. Returns None if the notebook doesn't exist"""
        return self._session.query(SagemakerNotebook).get(uri)

    def paginated_user_notebooks(self, username, groups, filter=None) -> dict:
        """Returns a page of user notebooks"""
        return paginate(
            query=self._query_user_notebooks(username, groups, filter),
            page=filter.get('page', NotebookRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', NotebookRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    def _query_user_notebooks(self, username, groups, filter) -> Query:
        query = self._session.query(SagemakerNotebook).filter(
            or_(
                SagemakerNotebook.owner == username,
                SagemakerNotebook.SamlAdminGroupName.in_(groups),
            )
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    SagemakerNotebook.description.ilike(term + '%%'),
                    SagemakerNotebook.label.ilike(term + '%%'),
                    SagemakerNotebook.tags.contains(
                        f'{{{NamingConventionService(pattern=NamingConventionPattern.DEFAULT_SEARCH, target_label=term).sanitize()}}}'
                    ),
                )
            )
        return query.order_by(SagemakerNotebook.label)

    def count_resources(self, environment_uri, group_uri):
        return (
            self._session.query(SagemakerNotebook)
            .filter(
                and_(
                    SagemakerNotebook.environmentUri == environment_uri,
                    SagemakerNotebook.SamlAdminGroupName == group_uri,
                )
            )
            .count()
        )
