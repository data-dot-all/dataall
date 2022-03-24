import os
import re

from engine.glue.glue_utils import ConfigReader
from engine.glue.handlers import query
from engine.glue.glue_utils.runner import Context
from engine.glue.handlers.query_resolution import resolve_query

def test_resolve_query_sql():
    query_handler = query.Query(type="query", name="my_query", config={"sql": "SELECT * FROM {{dataframe}}"})

    variables = {
        "dataframe": "titanic_raw",
        "pipeline_bucket": os.environ.get("BUCKET_NAME"),
        "pipeline_unittest_db": os.environ.get("UNITTEST_DB"),
    }
    args = {"STAGE": "test"}

    config_reader = ConfigReader(
        path="tests/customcode/glue/glue_jobs/titanic_ingestion.yaml", variables=variables, args=args
    )
    q = resolve_query(query_handler, "job", config_reader)
    assert q == "SELECT * FROM {}".format(variables["dataframe"])


def test_resolve_query_file():
    query_handler = query.Query(type="query", name="my_query", config={"file": "unittest.sql"})

    variables = {
        "dataframe": "titanic_raw",
        "pipeline_bucket": os.environ.get("BUCKET_NAME"),
        "pipeline_unittest_db": os.environ.get("UNITTEST_DB"),
    }
    args = {"STAGE": ""}

    config_reader = ConfigReader(
        path="tests/customcode/glue/glue_jobs/titanic_ingestion.yaml", variables=variables, args=args
    )
    q = resolve_query(query_handler, "job", config_reader)

    qry = re.sub(r"\n\s+", "", q).lower()

    assert (
        qry
        == "select passengerid,pclass,sex,age,sibsp,parch,ticket,fare,cabin,embarked from titanic_train_raw"
    )

def test_run_query_handler(spark_session):
    pax =  [ ("1", 10, "A"), ("2", 20, "B") ]
    columns = ["passenger_id","age", "cabin"]
    df= spark_session.createDataFrame(data=pax, schema = columns)
    df.createOrReplaceTempView("titanic_raw")

    query_handler = query.Query(type="query", name="my_query", config={"sql": "SELECT * FROM {{dataframe}}"})

    variables = {
        "dataframe": "titanic_raw",
        "pipeline_bucket": os.environ.get("BUCKET_NAME"),
        "pipeline_unittest_db": os.environ.get("UNITTEST_DB"),
    }
    args = {"STAGE": "test"}

    config_reader = ConfigReader(
        path="tests/customcode/glue/glue_jobs/titanic_ingestion.yaml", variables=variables, args=args
    )

    context = Context()
    query_handler.run_step(spark_session, config_reader, context = context)
    assert context.df("my_query")









