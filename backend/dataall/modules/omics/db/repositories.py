"""
DAO layer that encapsulates the logic and interaction with the database for notebooks
Provides the API to retrieve / update / delete notebooks
"""
from sqlalchemy import or_
from sqlalchemy.orm import Query

from dataall.db import paginate
from dataall.modules.omics.db.models import OmicsProject


class OmicsProjectRepository:
    """DAO layer for omics projects"""
    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 10

    def __init__(self, session):
        self._session = session

    def save_omics_project(self, omics_project):
        """Save omics project to the database"""
        self._session.add(omics_project)
        self._session.commit()

    def find_omics_project(self, uri) -> OmicsProject:
        """Finds a omics_project. Returns None if the omics project doesn't exist"""
        return self._session.query(OmicsProject).get(uri)

    def paginated_user_omics_projects(self, username, groups, filter=None) -> dict:
        """Returns a page of user omics projects"""
        return paginate(
            query=self._query_user_omics_projects(username, groups, filter),
            page=filter.get('page', OmicsProjectRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', OmicsProjectRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    def _query_user_omics_projects(self, username, groups, filter) -> Query:
        query = self._session.query(OmicsProject).filter(
            or_(
                OmicsProject.owner == username,
                OmicsProject.SamlAdminGroupName.in_(groups),
            )
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    OmicsProject.description.ilike(
                        filter.get('term') + '%%'
                    ),
                    OmicsProject.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query

    def count_omics_projects(self, environment_uri):
        return (
            self._session.query(OmicsProject)
            .filter(OmicsProject.environmentUri == environment_uri)
            .count()
        )
