import logging

from dataall.core.activity.db.activity_models import Activity
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.core.permissions.permission_checker import has_tenant_permission, has_resource_permission
from dataall.base.db import exceptions
from dataall.modules.worksheets.aws.athena_client import AthenaClient
from dataall.modules.worksheets.db.worksheet_models import Worksheet
from dataall.modules.worksheets.db.worksheet_repositories import WorksheetRepository
from dataall.modules.worksheets.services.worksheet_permissions import (
    MANAGE_WORKSHEETS,
    UPDATE_WORKSHEET,
    WORKSHEET_ALL,
    GET_WORKSHEET,
    DELETE_WORKSHEET,
    RUN_ATHENA_QUERY,
)


logger = logging.getLogger(__name__)


class WorksheetService:
    @staticmethod
    def get_worksheet_by_uri(session, uri: str) -> Worksheet:
        if not uri:
            raise exceptions.RequiredParameter(param_name='worksheetUri')
        worksheet = WorksheetRepository.find_worksheet_by_uri(session, uri)
        if not worksheet:
            raise exceptions.ObjectNotFound('Worksheet', uri)
        return worksheet

    @staticmethod
    @has_tenant_permission(MANAGE_WORKSHEETS)
    def create_worksheet(session, username, uri, data=None) -> Worksheet:
        worksheet = Worksheet(
            owner=username,
            label=data.get('label'),
            description=data.get('description', 'No description provided'),
            tags=data.get('tags'),
            chartConfig={'dimensions': [], 'measures': [], 'chartType': 'bar'},
            SamlAdminGroupName=data['SamlAdminGroupName'],
        )

        session.add(worksheet)
        session.commit()

        activity = Activity(
            action='WORKSHEET:CREATE',
            label='WORKSHEET:CREATE',
            owner=username,
            summary=f'{username} created worksheet {worksheet.name} ',
            targetUri=worksheet.worksheetUri,
            targetType='worksheet',
        )
        session.add(activity)

        ResourcePolicy.attach_resource_policy(
            session=session,
            group=data['SamlAdminGroupName'],
            permissions=WORKSHEET_ALL,
            resource_uri=worksheet.worksheetUri,
            resource_type=Worksheet.__name__,
        )
        return worksheet

    @staticmethod
    @has_resource_permission(UPDATE_WORKSHEET)
    def update_worksheet(session, username, uri, data=None):
        worksheet = WorksheetService.get_worksheet_by_uri(session, uri)
        for field in data.keys():
            setattr(worksheet, field, data.get(field))
        session.commit()

        activity = Activity(
            action='WORKSHEET:UPDATE',
            label='WORKSHEET:UPDATE',
            owner=username,
            summary=f'{username} updated worksheet {worksheet.name} ',
            targetUri=worksheet.worksheetUri,
            targetType='worksheet',
        )
        session.add(activity)
        return worksheet

    @staticmethod
    @has_resource_permission(GET_WORKSHEET)
    def get_worksheet(session, uri):
        worksheet = WorksheetService.get_worksheet_by_uri(session, uri)
        return worksheet

    @staticmethod
    @has_resource_permission(DELETE_WORKSHEET)
    def delete_worksheet(session, uri) -> bool:
        worksheet = WorksheetService.get_worksheet_by_uri(session, uri)
        session.delete(worksheet)
        ResourcePolicy.delete_resource_policy(
            session=session,
            group=worksheet.SamlAdminGroupName,
            resource_uri=uri,
            resource_type=Worksheet.__name__,
        )
        return True

    @staticmethod
    @has_resource_permission(RUN_ATHENA_QUERY)
    def run_sql_query(session, uri, worksheetUri, sqlQuery):
        environment = EnvironmentService.get_environment_by_uri(session, uri)
        worksheet = WorksheetService.get_worksheet_by_uri(session, worksheetUri)

        env_group = EnvironmentService.find_environment_group(
            session, worksheet.SamlAdminGroupName, environment.environmentUri
        )

        cursor = AthenaClient.run_athena_query(
            aws_account_id=environment.AwsAccountId,
            env_group=env_group,
            s3_staging_dir=f's3://{environment.EnvironmentDefaultBucketName}/athenaqueries/{env_group.environmentAthenaWorkGroup}/',
            region=environment.region,
            sql=sqlQuery,
        )

        return AthenaClient.convert_query_output(cursor)
