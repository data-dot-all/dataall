from .base_step import Step
from .observability import StepMetric


@Step(
    type="file",
    props_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "options": {
                "type": "object",
                "properties": {
                    "format": {"type": "string"},
                    "header": {"type": "boolean"},
                    "delimiter": {"type": "string"},
                    "inferSchema": {"type": "boolean"},
                },
            },
        },
        "required": ["path"],
    },
)
class FileInput:
    def run_step(self, spark, config, context, glueContext=None):
        self.logger.info("Inside Run Step")
        job_name = config.args.get("JOB_NAME")
        prefix = f"{self.name} [{self.type}]"
        self.logger.info(f"{prefix} READING {self.props.get('path')}")
        df = spark.read.load(self.props.get("path"), **self.props.get("options"))
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
