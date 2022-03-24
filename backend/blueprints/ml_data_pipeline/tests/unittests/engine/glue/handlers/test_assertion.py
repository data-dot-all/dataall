import os

from engine.glue.glue_utils import ConfigReader
from engine.glue.handlers import assertion
from engine.glue.glue_utils.runner import Context

def evaluate_query(self, df):
        nb_rows = df.count()
        sign = self.props.get("sign", "gt")
        return nb_rows, ((nb_rows > 0 and sign == "gt") or (nb_rows == 0 and sign == "eq"))

def test_evaluate_query(spark_session): 
   pax =  [ ("1", 10, "A"), ("2", 20, "B") ]
   columns = ["passenger_id","age", "cabin"]
   df= spark_session.createDataFrame(data=pax, schema = columns)
   df.createOrReplaceTempView("titanic_raw")
   assertion_handler = assertion.Assertion(type="assertion", name="my_assertion", config={"sql": "SELECT * FROM {{dataframe}} WHERE age <= 0"})

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
   assertion_handler_1 = assertion.Assertion(type="assertion", name="my_assertion", config={"sql": "SELECT * FROM {{dataframe}} WHERE age <= 0"})
   assertion_handler_1.run_step(spark_session, config_reader, context)

   assertion_handler_2 = assertion.Assertion(type="assertion", name="my_assertion", config={"sql": "SELECT * FROM {{dataframe}} WHERE age <= 0", "sign": "eq"})
   raise_exception = False
   try:
       assertion_handler_2.run_step(spark_session, config_reader, context)
   except :
       raise_exception = True
   assert raise_exception
    
