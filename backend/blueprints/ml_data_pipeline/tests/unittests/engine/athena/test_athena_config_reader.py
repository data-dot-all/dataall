import os
import re
from engine.athena import AthenaConfigReader


def test_athena_config_reader_steps():
    variables = {
        "dimension": "color",
        "path": "tests/customcode/athena/sql_queries",
    }
    args = {"STAGE": ""}

    config_reader = AthenaConfigReader(
        config_path="tests/customcode/athena/athena_jobs/dim_basic.yaml", variables=variables
    )
    steps = []
    for step in config_reader.steps:
        steps.append(step["name"])

    assert steps == ["Dim_color_01","Dim_color_02","Dim_color_03"]


def test_athena_config_reader_err():
    variables = {
        "pipeline_bucket": os.environ.get("BUCKET_NAME"),
        "pipeline_unittest_db": os.environ.get("UNITTEST_DB"),
    }
    args = {"STAGE": "test"}

    config_reader = AthenaConfigReader(
        config_path="tests/customcode/glue/glue_jobs/titanic_ingestion.yaml", variables=variables
    )

    read_success = False
    try:
        re.sub(r"\n\s+", "", config_reader.get_query("wrong_names.sql")).lower()
        read_success = True
    except Exception as e:
        print(e)

    assert not read_success

