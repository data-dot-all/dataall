from pyathena import connect
from dataall.base.aws.sts import SessionHelper


class AthenaClient:
    """Makes requests to AWS Athena"""

    @staticmethod
    def run_athena_query(aws_account_id, env_group, s3_staging_dir, region, sql=None):
        base_session = SessionHelper.remote_session(accountid=aws_account_id, region=region)
        boto3_session = SessionHelper.get_session(base_session=base_session, role_arn=env_group.environmentIAMRoleArn)
        creds = boto3_session.get_credentials()
        connection = connect(
            aws_access_key_id=creds.access_key,
            aws_secret_access_key=creds.secret_key,
            aws_session_token=creds.token,
            work_group=env_group.environmentAthenaWorkGroup,
            s3_staging_dir=s3_staging_dir,
            region_name=region,
        )
        cursor = connection.cursor()
        cursor.execute(sql)

        return cursor

    @staticmethod
    def convert_query_output(cursor):
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
