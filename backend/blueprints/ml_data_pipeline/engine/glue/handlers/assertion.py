from .base_step import Step
from .observability import StepMetric
from .query_resolution import resolve_query


@Step(
    type="assertion",
    props_schema={
        "type": "object",
        "properties": {
            "sql": {"type": "string"},
            "file": {"type": "string"},
            "sign": {"type": "string", "enum": ["lt", "gt", "lte", "gte", "eq"]},
        },
        "oneOf": [{"required": ["file"]}, {"required": ["sql"]}],
    },
)
class Assertion:
    def evaluate_query(self, df):
        nb_rows = df.count()
        sign = self.props.get("sign", "gt")
        return nb_rows, (
            (nb_rows > 0 and sign == "gt") or (nb_rows == 0 and sign == "eq")
        )

    def run_step(self, spark, config, context, glueContext=None):
        self.logger.info("Inside Run Step")
        """ Run a query that returns invalid items.
            When the count of the invalid items is > 1, 
            then the assertion is failed. 
        """
        self.logger.info(f"{self.name} Query")
        prefix = f"{self.name} [{self.type}]"
        processed = resolve_query(self, prefix, config)

        df = spark.sql(processed)

        nb_rows, assertion_break = self.evaluate_query(df)
        if assertion_break:
            self.emit_metric(
                StepMetric(
                    name=f"{self.name}:elapsed", value=self.elapsed, unit="Milliseconds"
                )
            )
            raise Exception("Assertion failed {}".format(nb_rows))
        else:
            self.success()
            self.emit_metric(
                StepMetric(
                    name=f"{self.name}:elapsed", value=self.elapsed, unit="Milliseconds"
                )
            )
