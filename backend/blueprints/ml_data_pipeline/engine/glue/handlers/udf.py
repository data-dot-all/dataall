import importlib

from .base_step import Step
from .observability import StepMetric


@Step(
    type="udf",
    props_schema={
        "type": "object",
        "properties": {
            "module": {"type": "string"},
            "function": {"type": "string"},
        },
        "required": ["module", "function"],
    },
)
class UserDefinedFunction:
    def run_step(self, spark, config, context, glueContext=None):
        self.logger.info("Inside Run Step")
        prefix = f"{self.name} [{self.type}]"
        self.logger.info(f"{prefix} Running {self.props.get('module')}")
        module = importlib.import_module(f"udfs.{self.props.get('module')}")
        print(
            "trying to get fx",
            self.props.get("function"),
            "from ",
            "udf.",
            self.props.get("module"),
        )
        fx = getattr(module, self.props.get("function", "udf"))
        print("running fx")
        fx(spark, ref=context.ref(self))
