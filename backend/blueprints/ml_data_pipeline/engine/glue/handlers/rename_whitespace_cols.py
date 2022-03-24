from .base_step import Step
from .observability import StepMetric


@Step(
    type="rename_whitespace_cols",
    props_schema={
        "type": "object",
        "properties": {
            "target": {"type": "string"},
        },
        "required": ["target"],
    },
)
class ReplaceWhiteSpaceCols:
    def run_step(self, spark, config, context, glueContext=None):
        self.logger.info("Inside Run Step")
        job_name = config.args.get("JOB_NAME")
        df_result = spark.sql("SELECT * FROM {}".format(self.props["target"]))

        for c in df_result.columns:
            df_result = df_result.withColumnRenamed(c, c.replace(" ", "_"))

        df_result.createOrReplaceTempView(self.name)
        context.register_df(self.name, df_result)
        self.emit_metric(
            StepMetric(
                name=f"{job_name}/{self.name}/count",
                value=df_result.rdd.countApprox(timeout=800, confidence=0.5),
            )
        )
