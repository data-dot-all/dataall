from dataall.api.constants import GraphQLEnumMapper
from dataall.base.db import exceptions
from dataall.modules.worksheets.db.models import Worksheet
from dataall.modules.worksheets.db.repositories import WorksheetRepository
from dataall.modules.worksheets.services.worksheet_services import WorksheetService
from dataall.api.context import Context


class WorksheetRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    NoPermission = '000'


def create_worksheet(context: Context, source, input: dict = None):
    if not input:
        raise exceptions.RequiredParameter(input)
    if not input.get('SamlAdminGroupName'):
        raise exceptions.RequiredParameter('groupUri')
    if not input.get('label'):
        raise exceptions.RequiredParameter('label')

    with context.engine.scoped_session() as session:
        return WorksheetService.create_worksheet(
            session=session,
            username=context.username,
            uri=None,
            data=input,
        )


def update_worksheet(
    context: Context, source, worksheetUri: str = None, input: dict = None
):
    with context.engine.scoped_session() as session:
        return WorksheetService.update_worksheet(
            session=session,
            username=context.username,
            uri=worksheetUri,
            data=input
        )


def get_worksheet(context: Context, source, worksheetUri: str = None):
    with context.engine.scoped_session() as session:
        return WorksheetService.get_worksheet(
            session=session,
            uri=worksheetUri,
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


def run_sql_query(
    context: Context, source, environmentUri: str = None, worksheetUri: str = None, sqlQuery: str = None
):
    with context.engine.scoped_session() as session:
        return WorksheetService.run_sql_query(
            session=session,
            uri=environmentUri,
            worksheetUri=worksheetUri,
            sqlQuery=sqlQuery
        )


def delete_worksheet(context, source, worksheetUri: str = None):
    with context.engine.scoped_session() as session:
        return WorksheetService.delete_worksheet(
            session=session,
            uri=worksheetUri
        )
