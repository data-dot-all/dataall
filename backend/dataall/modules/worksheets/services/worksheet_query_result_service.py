import csv
import io
import os
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from openpyxl import Workbook

from dataall.base.aws.s3_client import S3_client
from dataall.base.db import exceptions
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.modules.worksheets.db.worksheet_models import WorksheetQueryResult
from dataall.modules.worksheets.db.worksheet_repositories import WorksheetRepository
from dataall.modules.worksheets.services.worksheet_service import WorksheetService

if TYPE_CHECKING:
    try:
        from sqlalchemy.orm import Session
        from mypy_boto3_s3.client import S3Client
    except ImportError:
        print('skipping type checks as stubs are not installed')
        S3Client = None
        Session = None


class WorksheetQueryResultService:
    SupportedFormats = {'csv', 'xlsx'}

    @staticmethod
    def validate_input(data):
        if not data:
            raise exceptions.InvalidInput('data', data, 'input is required')
        if not data.get('athenaQueryId'):
            raise exceptions.RequiredParameter('athenaQueryId')
        if not data.get('fileFormat'):
            raise exceptions.RequiredParameter('fileFormat')
        if data.get('fileFormat', '').lower() not in WorksheetQueryResultService.SupportedFormats:
            raise exceptions.InvalidInput(
                'fileFormat', data.get('fileFormat'), ', '.join(WorksheetQueryResultService.SupportedFormats)
            )

    @staticmethod
    def get_output_bucket(session: 'Session', environment_uri: str) -> str:
        environment = EnvironmentService.get_environment_by_uri(session, environment_uri)
        bucket = environment.EnvironmentDefaultBucketName
        return bucket

    @staticmethod
    def create_query_result(
        environment_bucket: str, athena_workgroup: str, worksheet_uri: str, region: str, aws_account_id: str, data: dict
    ) -> WorksheetQueryResult:
        sql_query_result = WorksheetQueryResult(
            worksheetUri=worksheet_uri,
            AthenaQueryId=data.get('athenaQueryId'),
            fileFormat=data.get('fileFormat'),
            OutputLocation=f's3://{environment_bucket}/athenaqueries/{athena_workgroup}/',
            region=region,
            AwsAccountId=aws_account_id,
            queryType='data',
        )
        return sql_query_result

    @staticmethod
    def get_file_key(
        workgroup: str, query_id: str, file_format: str = 'csv', athena_queries_dir: str = 'athenaqueries'
    ) -> str:
        return f'{athena_queries_dir}/{workgroup}/{query_id}.{file_format}'

    @staticmethod
    def convert_csv_to_xlsx(csv_data) -> io.BytesIO:
        wb = Workbook()
        ws = wb.active
        csv_reader = csv.reader(csv_data.splitlines())
        for row in csv_reader:
            ws.append(row)

        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        return excel_buffer

    @staticmethod
    def handle_xlsx_format(output_bucket: str, file_key: str) -> bool:
        aws_region_name = os.getenv('AWS_REGION_NAME', 'eu-west-1')
        file_name, _ = file_key.split('.')
        csv_data = S3_client.get_object(region=aws_region_name, bucket=output_bucket, key=f'{file_name}.csv')
        excel_buffer = WorksheetQueryResultService.convert_csv_to_xlsx(csv_data)
        S3_client.put_object(region=aws_region_name, bucket=output_bucket, key=file_key, body=excel_buffer)
        return True

    @staticmethod
    def download_sql_query_result(session: 'Session', data: dict = None):
        # # default timeout for the download link is 2 hours(in minutes)
        default_timeout = os.getenv('QUERY_RESULT_TIMEOUT_MINUTES', 120)

        environment = EnvironmentService.get_environment_by_uri(session, data.get('environmentUri'))
        worksheet = WorksheetService.get_worksheet_by_uri(session, data.get('worksheetUri'))
        env_group = EnvironmentService.get_environment_group(
            session, worksheet.SamlAdminGroupName, environment.environmentUri
        )
        output_file_key = WorksheetQueryResultService.get_file_key(
            env_group.environmentAthenaWorkGroup, data.get('athenaQueryId'), data.get('fileFormat')
        )
        sql_query_result = WorksheetRepository.find_query_result_by_format(
            session, data.get('worksheetUri'), data.get('athenaQueryId'), data.get('fileFormat')
        )
        if data.get('fileFormat') == 'xlsx':
            is_job_failed = WorksheetQueryResultService.handle_xlsx_format(
                environment.EnvironmentDefaultBucketName, output_file_key
            )
            if is_job_failed:
                raise ValueError('Error while preparing the xlsx file')

        if not sql_query_result:
            sql_query_result = WorksheetQueryResultService.create_query_result(
                environment.EnvironmentDefaultBucketName,
                env_group.environmentAthenaWorkGroup,
                worksheet.worksheetUri,
                environment.region,
                environment.AwsAccountId,
                data,
            )
        S3_client.object_exists(
            region=environment.region, bucket=environment.EnvironmentDefaultBucketName, key=output_file_key
        )
        if sql_query_result.is_download_link_expired():
            url = S3_client.get_presigned_url(
                region=environment.region,
                bucket=environment.EnvironmentDefaultBucketName,
                key=output_file_key,
                expire_minutes=default_timeout,
            )
            sql_query_result.downloadLink = url
            sql_query_result.expiresIn = datetime.utcnow() + timedelta(seconds=default_timeout)

        session.add(sql_query_result)
        session.commit()

        return sql_query_result
