from pyathena import connect


def run_athena_query(session, work_group, s3_staging_dir, region, sql=None):
        creds = session.get_credentials()
        connection = connect(
            aws_access_key_id=creds.access_key,
            aws_secret_access_key=creds.secret_key,
            aws_session_token=creds.token,
            work_group=work_group,
            s3_staging_dir=s3_staging_dir,
            region_name=region,
        )
        cursor = connection.cursor()
        cursor.execute(sql)
        
        return cursor