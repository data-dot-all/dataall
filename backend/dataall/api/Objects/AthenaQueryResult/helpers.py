import nanoid
from pyathena import connect
from pyathena import result_set
from pyathena.async_cursor import AsyncCursor
from pyathena.model import AthenaQueryExecution

from ....db import models
from ....aws.handlers.sts import SessionHelper


def random_key():
    return nanoid.generate()


def run_query(context, environmentUri, sql):
    with context.engine.scoped_session() as session:
        e: models.Environment = session.query(models.Environment).get(environmentUri)
        if not e:
            raise Exception("ObjectNotFound")

        boto3_session = SessionHelper.remote_session(accountid=e.AwsAccountId)
        creds = boto3_session.get_credentials()
        connection = connect(
            aws_access_key_id=creds.access_key,
            aws_secret_access_key=creds.secret_key,
            aws_session_token=creds.token,
            work_group="primary",
            s3_staging_dir=f"s3://{e.EnvironmentDefaultBucketName}/preview/",
            region_name=e.region,
        )
        cursor = connection.cursor()
        cursor.execute(sql)
        columns = []
        for f in cursor.description:
            columns.append({"columnName": f[0], "typeName": "String"})

        rows = []
        for row in cursor:
            record = {"cells": []}
            for col_position, column in enumerate(columns):
                cell = {}
                cell["columnName"] = column["columnName"]
                cell["typeName"] = column["typeName"]
                cell["value"] = str(row[col_position])
                record["cells"].append(cell)
            rows.append(record)
    return {
        "error": None,
        "AthenaQueryId": cursor.query_id,
        "ElapsedTime": cursor.total_execution_time_in_millis,
        "rows": rows,
        "columns": columns,
    }


def parse_athena_result_set(resultset):
    columns = []
    for f in resultset.description:
        columns.append({"columnName": f[0], "typeName": "String"})
    rows = []
    for row in resultset:
        record = {"cells": []}
        for col_position, column in enumerate(columns):
            cell = {}
            cell["columnName"] = column["columnName"]
            cell["typeName"] = column["typeName"]
            cell["value"] = str(row[col_position])
            record["cells"].append(cell)
        rows.append(record)

    return {"rows": rows, "columns": columns}


def async_run_query(aws, region, bucket: str = None, key: str = None, sql=None, query_id=None):
    if not key:
        key = random_key()
    boto3_session = SessionHelper.remote_session(accountid=aws)
    creds = boto3_session.get_credentials()
    connection = connect(
        aws_access_key_id=creds.access_key,
        aws_secret_access_key=creds.secret_key,
        aws_session_token=creds.token,
        work_group="primary",
        s3_staging_dir=f"s3://{bucket}/{key}/",
        region_name=region,
        cursor_class=AsyncCursor,
    )
    cursor = connection.cursor()
    if query_id:
        # continuation
        query_execution = cursor._poll(query_id)
        if query_execution.state == AthenaQueryExecution.STATE_SUCCEEDED:
            results = result_set.AthenaResultSet(
                connection=connection,
                converter=cursor._converter,
                query_execution=query_execution,
                arraysize=cursor.arraysize,
                retry_config=cursor._retry_config,
            )

            data = parse_athena_result_set(resultset=results)
            return {
                **data,
                "Error": None,
                "OutputLocation": query_execution.output_location,
                "AthenaQueryId": query_id,
                "Status": query_execution.state,
                "ElapsedTime": query_execution.engine_execution_time_in_millis * 1000,
            }

        elif query_execution.state == AthenaQueryExecution.STATE_FAILED:
            return {
                "Error": "Query Failed",
                "AthenaQueryId": query_id,
                "Status": query_execution.state,
                "OutputLocation": query_execution.output_location,
                "ElapsedTime": query_execution.total_execution_time_in_millis * 1000,
                "rows": [],
                "columns": [],
            }
        return {
            "Error": None,
            "AthenaQueryId": query_id,
            "OutputLocation": query_execution.output_location,
            "Status": query_execution.state,
            "ElapsedTime": query_execution.total_execution_time_in_millis * 1000,
            "rows": [],
            "columns": [],
        }

    if sql:
        # first run

        with cursor._executor as executor:
            try:
                query_id, future = cursor.execute(sql)
                result = future.result()
                print("result ...", result.query_id)
                if result.state == AthenaQueryExecution.STATE_SUCCEEDED:
                    data = parse_athena_result_set(resultset=result)
                    return {
                        **data,
                        "Error": None,
                        "AthenaQueryId": query_id,
                        "Status": result.state,
                        "OutputLocation": result.output_location,
                        "ElapsedTime": result.engine_execution_time_in_millis * 1000,
                    }

                return {
                    "Error": None,
                    "AthenaQueryId": query_id,
                    "Status": result.state,
                    "OutputLocation": result.output_location,
                    "ElapsedTime": 0,
                    "rows": [],
                    "columns": [],
                }
            except Exception as e:
                return {
                    "Error": str(e),
                    "AthenaQueryId": query_id,
                    "Status": AthenaQueryExecution.STATE_FAILED,
                    "OutputLocation": None,
                    "ElapsedTime": 0,
                }


def async_run_query_on_environment(context, environmentUri, sql=None, query_id=None):
    with context.engine.scoped_session() as session:
        e: models.Environment = session.query(models.Environment).get(environmentUri)
        if not e:
            raise Exception("ObjectNotFound")

    return async_run_query(
        aws=e.AwsAccountId,
        region=e.region,
        bucket=e.EnvironmentDefaultBucketName,
        key=random_key(),
        sql=sql,
        query_id=query_id,
    )
