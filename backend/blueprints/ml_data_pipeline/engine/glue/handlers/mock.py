from .base_step import Step


@Step(
    type="mock",
    props_schema={
        "type": "object",
        "properties": {
            "message": {"type": "string"},
        },
        "required": ["message"],
    },
)
class MockStep:
    def run_step(self, spark, config, context, glueContext=None):
        self.logger.info("Inside Run Step")
        self.logger.info(f"Message: {self.props.get('message')}")
