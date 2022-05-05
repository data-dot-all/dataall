import copy
import logging
from datetime import datetime
from enum import Enum

import jsonschema
import tabulate

from .observability import StepMetric


class StepHandler:
    _instance = None

    def __init__(self):
        self.handlers = {}

    @staticmethod
    def add_handler(name, cls):
        StepHandler.get_instance().handlers[name] = cls

    @staticmethod
    def get_handler(step_input, config={}):
        _type = step_input.get("type")
        handler = StepHandler.get_instance().handlers.get(_type)
        if not handler:
            source_file = config.get("__source__", "")
            raise Exception(
                "Handler of type [{}] does not exist in [({}).{}]".format(_type, source_file, step_input.get("name"))
            )
        return handler

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = StepHandler()
        return cls._instance


class StepStatus(Enum):
    PARSED = "parsed"
    STARTED = "started"
    SUCCESS = "success"
    FAIL = "fail"


class StepInterface:
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "type": {"type": "string"},
            "name": {"type": "string"},
            "config": {"type": "object"},
        },
        "required": ["type", "name", "config"],
    }
    PROPS_SCHEMA = {"type": "object"}

    def __init__(self, **config):
        self.__class__.validate_config(config)
        self.__class__.validate_props(config["config"])
        self.type = config.get("type")
        self.name = config.get("name")
        self.props = config.get("config")
        self.handler = self.__class__.CLS
        self.logger = logging.getLogger()  # only used for init in unittests
        self.elapsed = -1
        self.metrics = []

    @classmethod
    def validate_config(cls, config):
        jsonschema.validate(config, schema=cls.CONFIG_SCHEMA)

    @classmethod
    def validate_props(cls, config):
        jsonschema.validate(config, schema=cls.PROPS_SCHEMA)

    def __str__(self):
        lines = [["name", self.name], ["type", self.type], ["handler", self.handler]]
        for p in self.__class__.PROPS_SCHEMA.get("properties"):
            lines.append([p, self.props.get(p, None)])

        return tabulate.tabulate(lines, headers=["Property", "Value"])

    @staticmethod
    def step_handler(type: str = None, props_schema: dict = None):
        def wrapper(cls):
            class Wrapped(cls, StepInterface):
                PROPS_SCHEMA = props_schema
                CONFIG_SCHEMA = StepInterface.CONFIG_SCHEMA
                CLS = cls.__name__

                def __init__(self, **config):
                    super().__init__(**config)

            StepHandler.add_handler(type, Wrapped)
            return Wrapped

        return wrapper

    @staticmethod
    def create_step(step_input, config={}):
        StepInterface.validate_props(step_input)
        handler = StepHandler.get_handler(step_input, config)
        return handler(**step_input)

    def emit_metric(self, metric):
        self.metrics.append(metric)

    def get_rendering_variables(self, args):
        variables = copy.deepcopy(self.props)
        variables.update(args)
        variables["stage"] = variables.get("STAGE", "")

        if variables["stage"] == "prod":
            variables["stage_"] = ""
        else:
            variables["stage_"] = variables["stage"]
        return variables

    def run_step(self, spark, config, context, glueContext=None):
        self.logger.warning("#run_step API not implemented")

    def run(self, spark, config, context, logger, glueContext=None):
        job_name = config.args.get("JOB_NAME")
        self.start = datetime.now()
        self.status = StepStatus.STARTED
        self.logger = logger

        try:

            self.run_step(spark=spark, config=config, context=context, glueContext=glueContext)
            self.success()

        except Exception as e:
            self.logger.exception(e)
            self.fail()
            raise e

        end = datetime.now()

        self.elapsed = (end - self.start).total_seconds()
        self.emit_metric(
            StepMetric(
                name=f"{job_name}/{self.name}/duration",
                value=self.elapsed,
                unit="Second",
            )
        )

    def success(self):
        self.status = StepStatus.SUCCESS
        self.logger.info(f"{self.name} [{self.type}] SUCCESS")

    def fail(self):
        self.status = StepStatus.FAIL
        self.logger.error(f"{self.name} [{self.type}] FAILED")

    def json(self, context):
        return {
            "name": self.name,
            "type": self.type,
            "status": self.status.value,
            "props": self.props,
            "duration": self.elapsed,
        }


Step = StepInterface.step_handler
