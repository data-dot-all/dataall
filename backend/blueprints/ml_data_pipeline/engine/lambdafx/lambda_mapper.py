import os
import uuid

from aws_cdk import aws_iam, aws_stepfunctions, core


class LambdaFxMappingException(Exception):
    def __init__(self, error, arg_name):
        super().__init__()
        self.message = f"Failed to create Lambda function for attribute `{arg_name}` due to error: `{error}`"
        self.error = error
        self.arg_name = arg_name

    def __str__(self):
        return self.message


class LambdaFxPropsMapper:
    """A class that parses the lambdafx configuration in the pipeline configuration file, and translates it into
    the CDK parameters.
    """

    @classmethod
    def map_function_props(cls, stack, function_name, config_props: dict) -> dict:
        """Creates the lambdafx function properties. A specific treatment for dead_letter_queue_enabled
        where the dead letter queue enabled is let undefined by default
        It also defines the default value for index and handler of lambdafx parameters to lambda_function.py and
        handler respectively.
        """
        lambdafx = dict(
            timeout=core.Duration.seconds(config_props.get("timeout", 900)),
            entry=cls.map_entry(config_props),
            environment=config_props.get("environment"),
            index=config_props.get("index", "lambda_function.py"),
            handler=config_props.get("handler", "handler"),
            role=cls.map_role(stack, function_name, config_props),
            layers=cls.map_layers(stack, function_name, config_props),
        )

        if config_props.get("dead_letter_queue_enabled") is not None:
            lambdafx["dead_letter_queue_enabled"] = config_props.get(
                "dead_letter_queue_enabled"
            )

        return lambdafx

    @classmethod
    def map_task_props(cls, lambda_function, config_props: dict) -> dict:

        lambdafx = dict(
            heartbeat=config_props.get("heartbeat"),
            input_path=config_props.get("input_path"),
            output_path=config_props.get("output_path"),
            result_path=config_props.get("result_path")
            or aws_stepfunctions.JsonPath.DISCARD,
            timeout=core.Duration.seconds(config_props.get("timeout", 900)),
            lambda_function=lambda_function,
            payload=aws_stepfunctions.TaskInput.from_object(config_props.get("payload"))
            if config_props.get("payload")
            else None,
            qualifier=None,
            payload_response_only=config_props.get("payload_response_only", True),
            retry_on_service_exceptions=config_props.get(
                "retry_on_service_exceptions", True
            ),
        )
        return lambdafx

    @classmethod
    def map_entry(cls, config_props):
        """Processes the entry item of lambdafx.
        By default, the entry of the codes is stored under customcode.

        Example:

            config:
               entry: "customcode/lambda_functions/prepare_iris"
               layer_ref:
                   - datascience_layer

        Parameters
           config_props: the configuration of the lambda_functions function in configuration file.

        """
        entry_point = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "..", "..", config_props["entry"])
        )
        return entry_point

    @classmethod
    def map_role(cls, stack, function_name, config_props):
        """Defines the role to be used by the lambdafx function. The role must be defined under 'role' section
        of config, for example:

            config:
                entry: "customcode/lambda_functions/prepare_iris"
                layer_ref:
                    - datascience_layer
                role: "myarnrole"

        When not defined, the environment role is used.

        Parameters
            stack the pipeline stack
            function_name the function name to be used to create the role.
            config_props the configuration of the lambdafx.
        """
        return aws_iam.Role.from_role_arn(
            stack,
            f"{function_name}Role-{str(uuid.uuid4())[:8]}",
            config_props.get("role", stack.pipeline_iam_role_arn),
            mutable=False,
        )

    @classmethod
    def map_layers(cls, stack, function_name, config_props):
        """Reads information of layers used by the lambdafx function.
        The lambdafx layer must be defined in aws_resource.

        """
        layers = []
        # Handles the layer_ref section
        for layer_ref in config_props.get("layer_ref", []):
            if stack.layer_versions.get(layer_ref):
                layers.append(stack.layer_versions.get(layer_ref))
            else:
                raise LambdaFxMappingException(
                    f"{layer_ref} is referenced by {function_name}, but not declared in aws_resource.",
                    "layers",
                )
        return layers
