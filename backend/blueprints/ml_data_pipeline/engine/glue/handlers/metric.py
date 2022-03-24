import pathlib

from jinja2 import Template

from .base_step import Step
from .observability import StepMetric


@Step(
    type="metric",
    props_schema={
        "type": "object",
        "properties": {
            "sql": {"type": "string"},
            "file": {"type": "string"},
            "dimensions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "sql": {"type": "string"},
                        "type": {"type": "string"},
                    },
                },
            },
            "measures": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "sql": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": ["count", "avg", "sum", "min", "max"],
                        },
                        "filters": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {"sql": {"type": "string"}},
                            },
                        },
                    },
                },
            },
        },
        "requires": ["measures", "dimensions"],
        "oneOf": [{"required": ["file"]}, {"required": ["sql"]}],
    },
)
class BusinessMetric:
    def run_step(self, spark, config, context, glueContext=None):
        self.logger.info("Inside Run Step")
        self.logger.info(f"  {self.name} Query")
        if self.props.get("sql"):
            query = self.props.get("sql")
        elif self.props.get("file"):
            p = (
                pathlib.PosixPath(config.query_dir, self.props.get("file"))
                .resolve()
                .as_posix()
            )
            with open(p, "r") as file:
                query = "\n".join(file.readlines())

        template = Template(query)
        processed = template.render(ref=context.ref(self))
        df = spark.sql(processed)

        self.success()
        self.emit_metric(
            StepMetric(name=f"{self.name}:count", value=df.rdd.countApprox())
        )
        self.emit_metric(
            StepMetric(
                name="f{self.name}:elasped", value=self.elapsed, unit="Milliseconds"
            )
        )
