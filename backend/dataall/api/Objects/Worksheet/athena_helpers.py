import nanoid

from ..AthenaQueryResult import AthenaQueryResult
from ....aws.handlers.sts import SessionHelper
from ....db import models


def connect(aws, region):
    return SessionHelper.remote_session(accountid=aws).client("athena", region_name=region)


def async_run_query(
    aws,
    region,
    bucket: str = None,
    key: str = None,
    sql=None,
    query_id=None,
    workgroup=None,
) -> AthenaQueryResult:
    client = connect(aws, region)
    if not key:
        key = nanoid.generate(size=12)
    if query_id:
        try:
            response = client.get_query_execution(QueryExecutionId=query_id)
        except client.exceptions.InvalidRequestException as e:
            return AthenaQueryResult(
                **{
                    "Error": str(e),
                    "Status": "FAILED",
                    "AthenaQueryId": query_id,
                    "ElapsedTimeInMs": None,
                    "DataScannedInBytes": None,
                    "OutputLocation": None,
                }
            )
        except client.exceptions.InternalServerException as e:
            return AthenaQueryResult(
                **{
                    "Error": str(e),
                    "Status": "FAILED",
                    "AthenaQueryId": query_id,
                }
            )

        config = response["QueryExecution"]["ResultConfiguration"]
        state = response["QueryExecution"]["Status"]
        stats = response["QueryExecution"]["Statistics"]
        print("==> athena stats", stats)
        if state["State"] == "SUCCEEDED":
            data = parse_query_results(client, query_id)
            return AthenaQueryResult(
                **{
                    **data,
                    "Error": None,
                    "Status": state["State"],
                    "AthenaQueryId": query_id,
                    "ElapsedTimeInMs": stats["TotalExecutionTimeInMillis"],
                    "DataScannedInBytes": stats["DataScannedInBytes"],
                    "OutputLocation": config["OutputLocation"],
                }
            )
        elif state["State"] in ["CANCELLED", "FAILED"]:
            return AthenaQueryResult(
                **{
                    "Error": state["StateChangeReason"],
                    "Status": state["State"],
                    "ElapsedTimeInMs": stats["TotalExecutionTimeInMillis"],
                    "DataScannedInBytes": stats["DataScannedInBytes"],
                    "AthenaQueryId": query_id,
                    "OutputLocation": config["OutputLocation"],
                }
            )
        elif state["State"] in ["RUNNING", "QUEUED"]:
            return AthenaQueryResult(
                **{
                    "Error": None,
                    "Status": state["State"],
                    "ElapsedTimeInMs": stats.get("TotalExecutionTimeInMillis", 0),
                    "DataScannedInBytes": 0,
                    "AthenaQueryId": query_id,
                    "OutputLocation": config["OutputLocation"],
                }
            )

    if sql:
        try:
            athena_workgroup = client.get_work_group(WorkGroup=workgroup)
            response = client.start_query_execution(
                QueryString=sql,
                ResultConfiguration={
                    "OutputLocation": f"s3://{bucket}/{key}/",
                    "EncryptionConfiguration": {"EncryptionOption": "SSE_S3"},
                },
                WorkGroup=athena_workgroup.get("WorkGroup", {}).get("Name", "primary"),
            )
            return AthenaQueryResult(
                **{
                    "AthenaQueryId": response["QueryExecutionId"],
                    "Status": "Submitted",
                    "OutputLocation": f"s3://{bucket}/{key}/",
                    "ElapsedTimeInMs": 0,
                }
            )
        except client.exceptions.InvalidRequestException as e:
            return AthenaQueryResult(
                **{
                    "Error": str(e),
                    "Status": "FAILED",
                    "AthenaQueryId": None,
                    "OutputLocation": f"s3://{bucket}/{key}/",
                    "ElapsedTimeInMs": 0,
                }
            )

    raise Exception("ProgrammingError")


def convert_row(row, columns):
    return [
        {
            "value": row["Data"][i].get("VarCharValue", ""),
            "columnName": columns[i]["Name"],
            "typeName": columns[i]["Type"],
        }
        for i, cell in enumerate(row["Data"])
    ]


def parse_query_results(client, query_id):
    response = client.get_query_results(QueryExecutionId=query_id, MaxResults=500)
    rows = response["ResultSet"]["Rows"]
    columns = response["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]
    return {
        "rows": [{"cells": convert_row(row, columns)} for row in rows[1:]],
        "columns": [{"columnName": column["Name"], "typeName": column["Type"]} for column in columns],
    }


def async_run_query_on_environment(
    environment: models.Environment,
    environment_group: models.EnvironmentGroup,
    sql=None,
    query_id=None,
) -> AthenaQueryResult:
    return async_run_query(
        aws=environment.AwsAccountId,
        region=environment.region,
        bucket=environment.EnvironmentDefaultBucketName,
        sql=sql,
        query_id=query_id,
        workgroup=environment_group.environmentAthenaWorkGroup,
    )
