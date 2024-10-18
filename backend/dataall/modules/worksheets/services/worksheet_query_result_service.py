import csv
import io
import os
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from openpyxl import Workbook

from dataall.base.db import exceptions
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.modules.worksheets.aws.s3_client import S3Client
from dataall.modules.worksheets.db.worksheet_models import WorksheetQueryResult
from dataall.modules.worksheets.db.worksheet_repositories import WorksheetRepository
from dataall.modules.worksheets.services.worksheet_enums import WorksheetResultsFormat
from dataall.modules.worksheets.services.worksheet_permissions import DOWNLOAD_ATHENA_QUERY_RESULTS, MANAGE_WORKSHEETS
from dataall.modules.worksheets.services.worksheet_service import WorksheetService

if TYPE_CHECKING:
    try:
        from sqlalchemy.orm import Session
        from openpyxl.worksheet.worksheet import Worksheet
    except ImportError:
        print('skipping type checks as stubs are not installed')
        Session = None
        Worksheet = None


class WorksheetQueryResultService:
    _DEFAULT_ATHENA_QUERIES_PATH = 'athenaqueries'
    _DEFAULT_QUERY_RESULTS_TIMEOUT = os.getenv('QUERY_RESULT_TIMEOUT_MINUTES', 120)

    @staticmethod
    def _create_query_result(
        environment_bucket: str, athena_workgroup: str, worksheet_uri: str, region: str, aws_account_id: str, data: dict
    ) -> WorksheetQueryResult:
        sql_query_result = WorksheetQueryResult(
            worksheetUri=worksheet_uri,
            AthenaQueryId=data.get('athenaQueryId'),
            fileFormat=data.get('fileFormat'),
            OutputLocation=f's3://{environment_bucket}/{WorksheetQueryResultService._DEFAULT_ATHENA_QUERIES_PATH}/{athena_workgroup}/',
            region=region,
            AwsAccountId=aws_account_id,
        )
        return sql_query_result

    @staticmethod
    def build_s3_file_path(workgroup: str, query_id: str, athena_queries_dir: str = None) -> str:
        athena_queries_dir = athena_queries_dir or WorksheetQueryResultService._DEFAULT_ATHENA_QUERIES_PATH
        return f'{athena_queries_dir}/{workgroup}/{query_id}'

    @staticmethod
    def convert_csv_to_xlsx(csv_data) -> io.BytesIO:
        wb = Workbook()
        ws: 'Worksheet' = wb.active
        csv_reader = csv.reader(csv_data.splitlines())
        for row in csv_reader:
            ws.append(row)

        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        return excel_buffer

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_WORKSHEETS)
    @ResourcePolicyService.has_resource_permission(DOWNLOAD_ATHENA_QUERY_RESULTS)
    def download_sql_query_result(session: 'Session', uri: str, env_uri: str, data: dict = None):
        environment = EnvironmentService.get_environment_by_uri(session, env_uri)
        worksheet = WorksheetService.get_worksheet_by_uri(session, uri)
        env_group = EnvironmentService.get_environment_group(
            session, worksheet.SamlAdminGroupName, environment.environmentUri
        )
        sql_query_result = WorksheetRepository.find_query_result_by_format(
            session, data.get('worksheetUri'), data.get('athenaQueryId'), data.get('fileFormat')
        )
        s3_client = S3Client(environment)
        if not sql_query_result:
            sql_query_result = WorksheetQueryResultService._create_query_result(
                environment.EnvironmentDefaultBucketName,
                env_group.environmentAthenaWorkGroup,
                worksheet.worksheetUri,
                environment.region,
                environment.AwsAccountId,
                data,
            )
        output_file_s3_path = WorksheetQueryResultService.build_s3_file_path(
            env_group.environmentAthenaWorkGroup, data.get('athenaQueryId')
        )
        if sql_query_result.fileFormat == WorksheetResultsFormat.XLSX.value:
            try:
                csv_data = s3_client.get_object(
                    bucket=environment.EnvironmentDefaultBucketName,
                    key=f'{output_file_s3_path}.{WorksheetResultsFormat.CSV.value}',
                )
                excel_buffer = WorksheetQueryResultService.convert_csv_to_xlsx(csv_data)
                s3_client.put_object(
                    bucket=environment.EnvironmentDefaultBucketName,
                    key=f'{output_file_s3_path}.{WorksheetResultsFormat.XLSX.value}',
                    body=excel_buffer,
                )
            except Exception as e:
                raise exceptions.AWSResourceNotAvailable('CONVERT_CSV_TO_EXCEL', f'Failed to convert csv to xlsx: {e}')

        s3_client.object_exists(
            bucket=environment.EnvironmentDefaultBucketName, key=f'{output_file_s3_path}.{sql_query_result.fileFormat}'
        )
        if sql_query_result.is_download_link_expired():
            url = s3_client.get_presigned_url(
                bucket=environment.EnvironmentDefaultBucketName,
                key=f'{output_file_s3_path}.{sql_query_result.fileFormat}',
                expire_minutes=WorksheetQueryResultService._DEFAULT_QUERY_RESULTS_TIMEOUT,
            )
            sql_query_result.downloadLink = url
            sql_query_result.expiresIn = datetime.utcnow() + timedelta(
                minutes=WorksheetQueryResultService._DEFAULT_QUERY_RESULTS_TIMEOUT
            )

        session.add(sql_query_result)
        session.commit()

        return sql_query_result
