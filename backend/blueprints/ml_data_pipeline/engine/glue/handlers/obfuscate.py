from pyspark.sql.functions import md5

from .base_step import Step
from .observability import StepMetric


@Step(
    type="obfuscate",
    props_schema={
        "type": "object",
        "properties": {
            "obfuscate_cols": {"type": "string"},
            "target": {"type": "string"},
        },
    },
)
class Obfuscate:
    def run_step(self, spark, config, context, glueContext=None):
        self.logger.info("Inside Run Step")
        # read props
        job_name = config.args.get("JOB_NAME")
        obfuscate_cols = self.props.get("obfuscate_cols").split(",")

        # create data frame
        df = context.df(self.props.get("target"))

        # md5 hash the required columns as specified in props
        for obfuscate_col in obfuscate_cols:
            df = df.withColumn(obfuscate_col, md5(obfuscate_col))

        # creata a resulting data from for use in subsequent sql_queries
        df.show()
        df.createOrReplaceTempView(self.name)
        context.register_df(self.name, df)

        self.emit_metric(
            StepMetric(
                name=f"{job_name}/{self.name}/count",
                unit="NbRecord",
                value=df.rdd.countApprox(timeout=800, confidence=0.5),
            )
        )
