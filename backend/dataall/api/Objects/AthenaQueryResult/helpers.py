import nanoid
from pyathena import connect

from ....db import models
from ....aws.handlers.sts import SessionHelper


def random_key():
    return nanoid.generate()


def run_query(environment: models.Environment, sql=None):

    boto3_session = SessionHelper.remote_session(accountid=environment.AwsAccountId)
    creds = boto3_session.get_credentials()
    connection = connect(
        aws_access_key_id=creds.access_key,
        aws_secret_access_key=creds.secret_key,
        aws_session_token=creds.token,
        work_group='primary',
        s3_staging_dir=f's3://{environment.EnvironmentDefaultBucketName}/preview/',
        region_name=environment.region,
    )
    cursor = connection.cursor()
    cursor.execute(sql)
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


def run_query_with_role(environment: models.Environment, environment_group: models.EnvironmentGroup, sql=None):
    base_session = SessionHelper.remote_session(accountid=environment.AwsAccountId)
    boto3_session = SessionHelper.get_session(base_session=base_session, role_arn=environment_group.environmentIAMRoleArn)
    creds = boto3_session.get_credentials()
    connection = connect(
        aws_access_key_id=creds.access_key,
        aws_secret_access_key=creds.secret_key,
        aws_session_token=creds.token,
        work_group=environment_group.environmentAthenaWorkGroup,
        s3_staging_dir=f's3://{environment.EnvironmentDefaultBucketName}/preview/',
        region_name=environment.region,
    )
    cursor = connection.cursor()
    cursor.execute(sql)
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
