from sqlalchemy import and_

from .... import db
from ..Worksheet import athena_helpers
from ....api.constants import WorksheetRole
from ....api.context import Context
from ....db import paginate, exceptions, permissions, models
from ....db.api import ResourcePolicy


def create_worksheet(context: Context, source, input: dict = None):
    with context.engine.scoped_session() as session:
        return db.api.Worksheet.create_worksheet(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=input,
            check_perm=True,
        )


def update_worksheet(context: Context, source, worksheetUri: str = None, input: dict = None):
    with context.engine.scoped_session() as session:
        return db.api.Worksheet.update_worksheet(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=worksheetUri,
            data=input,
            check_perm=True,
        )


def get_worksheet(context: Context, source, worksheetUri: str = None):
    with context.engine.scoped_session() as session:
        return db.api.Worksheet.get_worksheet(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=worksheetUri,
            data=None,
            check_perm=True,
        )


def resolve_user_role(context: Context, source: models.Worksheet):
    if context.username and source.owner == context.username:
        return WorksheetRole.Creator.value
    elif context.groups and source.SamlAdminGroupName in context.groups:
        return WorksheetRole.Admin.value
    return WorksheetRole.NoPermission.value


def list_worksheets(context, source, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Worksheet.paginated_user_worksheets(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )


def share_worksheet(context: Context, source, worksheetUri: str = None, input: dict = None):
    with context.engine.scoped_session() as session:
        return db.api.Worksheet.share_worksheet(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=worksheetUri,
            data=input,
            check_perm=True,
        )


def update_worksheet_share(context, source, worksheetShareUri: str = None, canEdit: bool = None):
    with context.engine.scoped_session() as session:
        share: models.WorksheetShare = session.query(models.WorksheetShare).get(worksheetShareUri)
        if not share:
            raise exceptions.ObjectNotFound("WorksheetShare", worksheetShareUri)

        return db.api.Worksheet.update_share_worksheet(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=share.worksheetUri,
            data={"canEdit": canEdit, "share": share},
            check_perm=True,
        )

    return share


def remove_worksheet_share(context, source, worksheetShareUri):
    with context.engine.scoped_session() as session:
        share: models.WorksheetShare = session.query(models.WorksheetShare).get(worksheetShareUri)
        if not share:
            raise exceptions.ObjectNotFound("WorksheetShare", worksheetShareUri)

        return db.api.Worksheet.delete_share_worksheet(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=share.worksheetUri,
            data={"share": share},
            check_perm=True,
        )


def resolve_shares(context: Context, source: models.Worksheet, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        q = session.query(models.WorksheetShare).filter(models.WorksheetShare.worksheetUri == source.worksheetUri)
    return paginate(q, page_size=filter.get("pageSize", 15), page=filter.get("page", 1)).to_dict()


def start_query(context, source, worksheetUri: str = None, input: dict = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=worksheetUri,
            permission_name=permissions.RUN_WORKSHEET_QUERY,
        )

        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=input["environmentUri"],
            permission_name=permissions.RUN_ATHENA_QUERY,
        )

        environment = db.api.Environment.get_environment_by_uri(session, input["environmentUri"])

        worksheet = db.api.Worksheet.get_worksheet_by_uri(session, worksheetUri)

        env_group = db.api.Environment.get_environment_group(
            session, worksheet.SamlAdminGroupName, environment.environmentUri
        )

        athena_response = athena_helpers.async_run_query_on_environment(
            environment=environment,
            environment_group=env_group,
            sql=input.get("sqlBody", None),
            query_id=input.get("AthenaQueryId", None),
        )
        if not athena_response.Error:
            result = models.WorksheetQueryResult(
                worksheetUri=worksheetUri,
                queryType="data",
                AwsAccountId=environment.AwsAccountId,
                region=environment.region,
                AthenaQueryId=athena_response.AthenaQueryId,
                OutputLocation=athena_response.OutputLocation,
                sqlBody=input.get("sqlBody"),
                error=athena_response.Error,
                status=athena_response.Status,
            )
            session.add(result)
    return athena_response.to_dict()


def poll_query(context, source, worksheetUri: str = None, AthenaQueryId: str = None):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=worksheetUri,
            permission_name=permissions.RUN_WORKSHEET_QUERY,
        )

        result: models.WorksheetQueryResult = session.query(models.WorksheetQueryResult).get(AthenaQueryId)

        if not result:
            raise exceptions.AWSResourceNotFound(action="Poll Athena Query", message="Query not found on Amazon Athena")

        poll_result = athena_helpers.async_run_query(
            aws=result.AwsAccountId, region=result.region, query_id=result.AthenaQueryId
        )

        if poll_result.Status != result.status:
            result.status = poll_result.Status
            result.ElapsedTimeInMs = poll_result.ElapsedTimeInMs
            result.DataScannedInBytes = poll_result.DataScannedInBytes
            result.error = poll_result.Error

        return poll_result.to_dict()


def resolve_last_saved_query_result(context: Context, source: models.Worksheet):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=source.worksheetUri,
            permission_name=permissions.GET_WORKSHEET,
        )
        last_query = (
            session.query(models.WorksheetQueryResult)
            .filter(
                and_(
                    models.WorksheetQueryResult.worksheetUri == source.worksheetUri,
                    models.WorksheetQueryResult.queryType == "data",
                    models.WorksheetQueryResult.status == "SUCCEEDED",
                )
            )
            .order_by(models.WorksheetQueryResult.created.desc())
            .first()
        )
        if last_query:
            poll_result = athena_helpers.async_run_query(
                aws=last_query.AwsAccountId,
                region=last_query.region,
                query_id=last_query.AthenaQueryId,
            )
        else:
            poll_result = None
    return poll_result


def delete_worksheet(context, source, worksheetUri: str = None):
    with context.engine.scoped_session() as session:
        return db.api.Worksheet.delete_worksheet(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=worksheetUri,
            data=None,
            check_perm=True,
        )
