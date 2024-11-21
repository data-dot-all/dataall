from dataall.base.db import exceptions
from dataall.modules.worksheets.api.enums import WorksheetRole
from dataall.modules.worksheets.db.worksheet_models import Worksheet
from dataall.modules.worksheets.db.worksheet_repositories import WorksheetRepository
from dataall.modules.worksheets.services.worksheet_service import WorksheetService
from dataall.base.api.context import Context


def create_worksheet(context: Context, source, input: dict = None):
    if not input:
        raise exceptions.RequiredParameter(input)
    if not input.get('SamlAdminGroupName'):
        raise exceptions.RequiredParameter('groupUri')
    if not input.get('label'):
        raise exceptions.RequiredParameter('label')

    return WorksheetService.create_worksheet(data=input)


def update_worksheet(context: Context, source, worksheetUri: str = None, input: dict = None):
    return WorksheetService.update_worksheet(uri=worksheetUri, data=input)


def get_worksheet(context: Context, source, worksheetUri: str = None):
    return WorksheetService.get_worksheet(uri=worksheetUri)


def resolve_user_role(context: Context, source: Worksheet):
    if context.username and source.owner == context.username:
        return WorksheetRole.Creator.value
    elif context.groups and source.SamlAdminGroupName in context.groups:
        return WorksheetRole.Admin.value
    return WorksheetRole.NoPermission.value


def list_worksheets(context, source, filter: dict = None):
    if not filter:
        filter = {}
    return WorksheetService.list_user_worksheets(filter)


def run_sql_query(context: Context, source, environmentUri: str = None, worksheetUri: str = None, sqlQuery: str = None):
    return WorksheetService.run_sql_query(uri=environmentUri, worksheetUri=worksheetUri, sqlQuery=sqlQuery)


def delete_worksheet(context, source, worksheetUri: str = None):
    return WorksheetService.delete_worksheet(uri=worksheetUri)
