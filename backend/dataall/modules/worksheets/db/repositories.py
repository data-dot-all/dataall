"""
DAO layer that encapsulates the logic and interaction with the database for worksheets
"""
from sqlalchemy import or_, and_
from sqlalchemy.orm import Query

from dataall.db import paginate
from dataall.modules.worksheets.db.models import Worksheet, WorksheetShare


class WorksheetRepository:
    """DAO layer for worksheets"""
    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 10

    def __init__(self, session):
        self._session = session

    @classmethod
    def find_worksheet_by_uri(self, uri) -> Worksheet:
        return self._session.query(Worksheet).get(uri)
    
    @classmethod
    def query_user_worksheets(self, username, groups, filter) -> Query:
        query = self._session.query(Worksheet).filter(
            or_(
                Worksheet.owner == username,
                Worksheet.SamlAdminGroupName.in_(groups),
            )
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    Worksheet.label.ilike('%' + filter.get('term') + '%'),
                    Worksheet.description.ilike('%' + filter.get('term') + '%'),
                    Worksheet.tags.contains(f"{{{filter.get('term')}}}"),
                )
            )
        return query

    @classmethod
    def paginated_user_worksheets(
        self, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=self.query_user_worksheets(username, groups, data),
            page=data.get('page', self._DEFAULT_PAGE),
            page_size=data.get('pageSize', self._DEFAULT_PAGE_SIZE),
        ).to_dict()
    
    @classmethod
    def get_worksheet_share(self, uri, data) -> WorksheetShare:
        return (
            self._session.query(WorksheetShare)
            .filter(
                and_(
                    WorksheetShare.worksheetUri == uri,
                    WorksheetShare.principalId == data.get('principalId'),
                    WorksheetShare.principalType == data.get('principalType'),
                )
            )
            .first()
        )
