

from dataall.modules.worksheets.api.schema import WorksheetRole
from dataall.modules.worksheets.db.models import Worksheet, WorksheetShare
from dataall.modules.worksheets.db.repositories import WorksheetRepository
from dataall.modules.worksheets.services.worksheet_services import WorksheetService
from dataall.api.context import Context
from dataall.db import paginate, exceptions


def create_worksheet(context: Context, source, input: dict = None):
    with context.engine.scoped_session() as session:
        return WorksheetService.create_worksheet(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=input,
            check_perm=True,
        )


def update_worksheet(
    context: Context, source, worksheetUri: str = None, input: dict = None
):
    with context.engine.scoped_session() as session:
        return WorksheetService.update_worksheet(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=worksheetUri,
            data=input,
            check_perm=True,
        )


def get_worksheet(context: Context, source, worksheetUri: str = None):
    with context.engine.scoped_session() as session:
        return WorksheetService.get_worksheet(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=worksheetUri,
            data=None,
            check_perm=True,
        )


def resolve_user_role(context: Context, source: Worksheet):
    if context.username and source.owner == context.username:
        return WorksheetRole.Creator.value
    elif context.groups and source.SamlAdminGroupName in context.groups:
        return WorksheetRole.Admin.value
    return WorksheetRole.NoPermission.value


def list_worksheets(context, source, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return WorksheetRepository.paginated_user_worksheets(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )


def share_worksheet(
    context: Context, source, worksheetUri: str = None, input: dict = None
):
    with context.engine.scoped_session() as session:
        return WorksheetService.share_worksheet(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=worksheetUri,
            data=input,
            check_perm=True,
        )


def update_worksheet_share(
    context, source, worksheetShareUri: str = None, canEdit: bool = None
):
    with context.engine.scoped_session() as session:
        share: WorksheetShare = WorksheetRepository.find_worksheet_share_by_uri(
            session, worksheetShareUri)
        if not share:
            raise exceptions.ObjectNotFound('WorksheetShare', worksheetShareUri)

        return WorksheetService.update_share_worksheet(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=share.worksheetUri,
            data={'canEdit': canEdit, 'share': share},
            check_perm=True,
        )

    return share


def remove_worksheet_share(context, source, worksheetShareUri):
    with context.engine.scoped_session() as session:
        share: WorksheetShare = WorksheetRepository.find_worksheet_share_by_uri(
            session, worksheetShareUri)
        if not share:
            raise exceptions.ObjectNotFound('WorksheetShare', worksheetShareUri)

        return WorksheetService.delete_share_worksheet(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=share.worksheetUri,
            data={'share': share},
            check_perm=True,
        )


def resolve_shares(context: Context, source: Worksheet, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        q = session.query(WorksheetShare).filter(
            WorksheetShare.worksheetUri == source.worksheetUri
        )
    return paginate(
        q, page_size=filter.get('pageSize', 15), page=filter.get('page', 1)
    ).to_dict()


def run_sql_query(
    context: Context, source, environmentUri: str = None, worksheetUri: str = None, sqlQuery: str = None
):
    with context.engine.scoped_session() as session:
        return WorksheetService.run_sql_query(
            session=session,
            username=context.username,
            groups=context.groups,
            environmentUri=environmentUri,
            worksheetUri=worksheetUri,
            sqlQuery=sqlQuery
        )


def delete_worksheet(context, source, worksheetUri: str = None):
    with context.engine.scoped_session() as session:
        return WorksheetService.delete_worksheet(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=worksheetUri,
            data=None,
            check_perm=True,
        )
