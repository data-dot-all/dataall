"""
DAO layer that encapsulates the logic and interaction with the database for worksheets
"""

from sqlalchemy import or_
from sqlalchemy.orm import Query

from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.base.db import paginate
from dataall.modules.worksheets.db.worksheet_models import Worksheet, WorksheetQueryResult
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)


class WorksheetRepository(EnvironmentResource):
    """DAO layer for worksheets"""

    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 10

    @staticmethod
    def count_resources(session, environment, group_uri) -> int:
        return (
            session.query(WorksheetQueryResult)
            .filter(WorksheetQueryResult.AwsAccountId == environment.AwsAccountId)
            .count()
        )

    @staticmethod
    def find_worksheet_by_uri(session, uri) -> Worksheet:
        return session.query(Worksheet).get(uri)

    @staticmethod
    def query_user_worksheets(session, username, groups, filter) -> Query:
        query = session.query(Worksheet).filter(
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
                    Worksheet.tags.contains(
                        f'{{{NamingConventionService(pattern=NamingConventionPattern.DEFAULT_SEARCH, target_label=filter.get("term")).sanitize()}}}'
                    ),
                )
            )
        return query.order_by(Worksheet.label)

    @staticmethod
    def paginated_user_worksheets(session, username, groups, uri, data=None, check_perm=None) -> dict:
        return paginate(
            query=WorksheetRepository.query_user_worksheets(session, username, groups, data),
            page=data.get('page', WorksheetRepository._DEFAULT_PAGE),
            page_size=data.get('pageSize', WorksheetRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()
