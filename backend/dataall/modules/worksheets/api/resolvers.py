from dataall.base.db import exceptions
from dataall.modules.worksheets.services.worksheet_enums import WorksheetRole, WorksheetResultsFormat
from dataall.modules.worksheets.db.worksheet_models import Worksheet
from dataall.modules.worksheets.db.worksheet_repositories import WorksheetRepository
from dataall.modules.worksheets.services.worksheet_service import WorksheetService
from dataall.base.api.context import Context
from dataall.modules.worksheets.services.worksheet_query_result_service import WorksheetQueryResultService


def create_worksheet(context: Context, source, input: dict = None):
    if not input:
        raise exceptions.RequiredParameter(input)
    if not input.get('SamlAdminGroupName'):
        raise exceptions.RequiredParameter('groupUri')
    if input.get('SamlAdminGroupName') not in context.groups:
        raise exceptions.InvalidInput('groupUri', input.get('SamlAdminGroupName'), " a user's groups")

    if not input.get('label'):
        raise exceptions.RequiredParameter('label')

    with context.engine.scoped_session() as session:
        return WorksheetService.create_worksheet(
            session=session,
            username=context.username,
            data=input,
        )


def update_worksheet(context: Context, source, worksheetUri: str = None, input: dict = None):
    with context.engine.scoped_session() as session:
        return WorksheetService.update_worksheet(
            session=session, username=context.username, uri=worksheetUri, data=input
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


def run_sql_query(context: Context, source, environmentUri: str = None, worksheetUri: str = None, sqlQuery: str = None):
    with context.engine.scoped_session() as session:
        return WorksheetService.run_sql_query(
            session=session, uri=environmentUri, worksheetUri=worksheetUri, sqlQuery=sqlQuery
        )


def delete_worksheet(context, source, worksheetUri: str = None):
    with context.engine.scoped_session() as session:
        return WorksheetService.delete_worksheet(session=session, uri=worksheetUri)


def create_athena_query_result_download_url(context: Context, source, input: dict = None):
    if not input:
        raise exceptions.RequiredParameter('data')
    if not input.get('environmentUri'):
        raise exceptions.RequiredParameter('environmentUri')
    if not input.get('athenaQueryId'):
        raise exceptions.RequiredParameter('athenaQueryId')
    if not input.get('fileFormat'):
        raise exceptions.RequiredParameter('fileFormat')
    if not hasattr(WorksheetResultsFormat, input.get('fileFormat').upper()):
        raise exceptions.InvalidInput(
            'fileFormat',
            input.get('fileFormat'),
            ', '.join(result_format.value for result_format in WorksheetResultsFormat),
        )

    env_uri = input['environmentUri']
    worksheet_uri = input['worksheetUri']

    with context.engine.scoped_session() as session:
        return WorksheetQueryResultService.download_sql_query_result(
            session=session, uri=worksheet_uri, env_uri=env_uri, data=input
        )
