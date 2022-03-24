import os
import re
from engine.glue.glue_utils import ConfigReader


def test_config_reader():
    variables = {
        "pipeline_bucket": os.environ.get("BUCKET_NAME"),
        "pipeline_unittest_db": os.environ.get("UNITTEST_DB"),
    }
    args = {"STAGE": ""}

    config_reader = ConfigReader(
        path="tests/customcode/glue/glue_jobs/titanic_ingestion.yaml", variables=variables, args=args
    )
    steps = [(step.name, step.handler) for step in config_reader.steps_definition]

    assert steps == [
        ("titanic_train_raw", "S3FileInput"),
        ("prepared_titanic", "Query"),
        ("titanic_materialize", "Save"),
    ]

    query = re.sub(r"\n\s+", "", config_reader.get_query("unittest.sql")).lower()

    assert (
        query
        == "select passengerid,pclass,sex,age,sibsp,parch,ticket,fare,cabin,embarked from titanic_train_raw"
    )


def test_config_reader_err():
    variables = {
        "pipeline_bucket": os.environ.get("BUCKET_NAME"),
        "pipeline_unittest_db": os.environ.get("UNITTEST_DB"),
    }
    args = {"STAGE": "test"}

    config_reader = ConfigReader(
        path="tests/customcode/glue/glue_jobs/titanic_ingestion.yaml", variables=variables, args=args
    )

    read_success = False
    try:
        re.sub(r"\n\s+", "", config_reader.get_query("wrong_names.sql")).lower()
        read_success = True
    except Exception as e:
        print(e)

    assert not read_success


def test_config_reader_from_string():
    config = """
    queries: "tests/customcode/glue/sql_queries"
    steps:

        - name: titanic_train_raw
          type : s3
          config:
            bucket: {{ pipeline_bucket }}
            prefix: "data/titanic/train.csv"
            options:
                format : csv
                inferSchema: true
                sep: ","
                header : true

        - name: prepared_titanic
          type: query
          config:
            file: unittest.sql

        - name : titanic_materialize
          type: materialize
          config:
            target: prepared_titanic
            database:  {{ pipeline_unittest_db }}
            table: titanic
            bucket: {{ pipeline_bucket }}
            prefix: data/titanic/ingested/train
            options:
                format: parquet
            description: "Ingested Titanic dataset"
    """
    variables = {
        "pipeline_bucket": os.environ.get("BUCKET_NAME"),
        "pipeline_unittest_db": os.environ.get("UNITTEST_DB"),
    }
    args = {}

    config_reader = ConfigReader(path=None, config=config, variables=variables, args=args)

    steps = [(step.name, step.handler) for step in config_reader.steps_definition]

    assert steps == [
        ("titanic_train_raw", "S3FileInput"),
        ("prepared_titanic", "Query"),
        ("titanic_materialize", "Save"),
    ]
