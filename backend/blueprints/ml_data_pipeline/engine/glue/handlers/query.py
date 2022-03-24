from .base_step import Step
from .observability import StepMetric
from .query_resolution import resolve_query


@Step(
    type="query",
    props_schema={
        "type": "object",
        "properties": {
            "sql": {"type": "string"},
            "file": {"type": "string"},
        },
        "oneOf": [{"required": ["file"]}, {"required": ["sql"]}],
    },
)
class Query:
    def run_step(self, spark, config, context, glueContext=None):
        self.logger.info("Inside Run Step")
        job_name = config.args.get("JOB_NAME")
        prefix = f"{self.name} [{self.type}]"

        processed = resolve_query(self, prefix, config)

        df = spark.sql(processed)

        df.createOrReplaceTempView(self.name)
        context.register_df(self.name, df)
        self.emit_metric(
            StepMetric(
                name=f"{job_name}/{self.name}/count",
                value=df.rdd.countApprox(timeout=800, confidence=0.5),
            )
        )
