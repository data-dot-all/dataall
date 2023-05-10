from dataall import db
from dataall.aws.handlers.sts import SessionHelper
from dataall.modules.common.athena.athena_client import run_athena_query
from dataall.modules.worksheets.api.schema import WorksheetRole
from dataall.modules.worksheets.db.models import Worksheet, WorksheetShare
from dataall.modules.worksheets.db.repositories import WorksheetRepository
from dataall.modules.worksheets.services.services import WorksheetService
from dataall.api.context import Context
from dataall.db import paginate, exceptions, permissions
from dataall.db.api import ResourcePolicy


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
        return WorksheetRepository(session).paginated_user_worksheets(
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
        share: WorksheetShare = session.query(WorksheetShare).get(
            worksheetShareUri
        )
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
        share: WorksheetShare = session.query(WorksheetShare).get(
            worksheetShareUri
        )
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
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=environmentUri,
            permission_name=permissions.RUN_ATHENA_QUERY,
        )
        environment = db.api.Environment.get_environment_by_uri(session, environmentUri)
        worksheet = WorksheetService.get_worksheet_by_uri(session, worksheetUri)

        env_group = db.api.Environment.get_environment_group(
            session, worksheet.SamlAdminGroupName, environment.environmentUri
        )

    base_session = SessionHelper.remote_session(accountid=environment.AwsAccountId)
    boto3_session = SessionHelper.get_session(base_session=base_session, role_arn=env_group.environmentIAMRoleArn)
    
    cursor = run_athena_query(
        session=boto3_session,
        work_group=env_group.environmentAthenaWorkGroup,
        s3_staging_dir=f's3://{environment.EnvironmentDefaultBucketName}/athenaqueries/{env_group.environmentAthenaWorkGroup}/',
        region=environment.region,
        sql=sqlQuery
    )

    columns = []
    for f in cursor.description:
        columns.append({'columnName': f[0], 'typeName': 'String'})

    rows = []
    for row in cursor:
        record = {'cells': []}
        for col_position, column in enumerate(columns):
            cell = {}
            cell['columnName'] = column['columnName']
            cell['typeName'] = column['typeName']
            cell['value'] = str(row[col_position])
            record['cells'].append(cell)
        rows.append(record)
    return {
        'error': None,
        'AthenaQueryId': cursor.query_id,
        'ElapsedTime': cursor.total_execution_time_in_millis,
        'rows': rows,
        'columns': columns,
    }


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
