from engine import resource_task
from aws_cdk import core


class ATestStack(core.Stack):
    def __init__(self, **kwargs):
        super().__init__(None, **kwargs)
        self.env = {
            "CDK_DEFAULT_ACCOUNT": "012345678912",
            "CDK_DEFAULT_REGION": "eu-west-1",
        }
        self.pipeline_iam_role_arn = "arn:aws:iam::012345678901:role/dhdatasciencedevoqtnpj"
        self.pipeline_fulldev_iam_role = "arn:aws:iam::012345678901:role/dhdatasciencedevoqtnpj"
        self.pipeline_admin_iam_role = "arn:aws:iam::012345678901:role/dhdatasciencedevoqtnpj"
        self.ecr_repository_uri = "dkr.012345678912.eu-west-1"
        self.layer_versions = {}
        self.pipeline_name = "pl"
        self.stage = "test"
        self.resource_tags = {"tag1": "tag1_value"}
        self.tags_tracker = {}
        self.commit_id = "CID"
        self.build_id = "BID"

    def set_resource_tags(self, resource):
        """ Puts the tag to the resource """
        for key, value in self.resource_tags.items():
            core.Tags.of(resource).add(key, value)
            self.tags_tracker[resource] = {key: value}


def test_code_asset():
    """ Tests code creation from asset. At this stage, nothing really happens"""
    code = resource_task.code_from_path_and_cmd(
        "customcode/lambda_layers/pandasx", "echo hi", resource_task.lambda_to_runtime({"config": {}})
    )

    # Because nothing happens, although the path does not exist, the code asset object is created anyway
    assert code


def test_make_lambda_layer():
    stack = ATestStack()
    cmd = """rm -rf /asset-output/python  &&
                    pip install -r requirements.txt --target /asset-output/python  &&
                    rm -rf /asset-output/python/scipy* && rm -rf /asset-output/python/numpy*
          """

    lv = resource_task.make_lambda_layer(
        stack, "pandas", "customcode/lambda_layers/pandas", resource_task.lambda_to_runtime({"config": {}}), cmd
    )
    assert lv
    assert len(lv.compatible_runtimes) == 1
    assert lv.compatible_runtimes[0].name == resource_task.lambda_to_runtime({"config": {}}).name



def test_make_lambda_function_trigger():
    stack = ATestStack()
    resource = {
        "name": "trigger_fn",
        "type": "lambda_function",
        "config": {
            "entry": "tests/customcode/lambda_functions/example_1_fx",
            "index": "example_handler.py",
            "handler": "handler",
            "runtime": "python3.8",
        },
    }
    fn, _ = resource_task.make_lambda_function_trigger(stack, resource, "arn:aws:iam::012345678901:statemachine/statemachnie", "bucket", "test","ad_group_admin")
    assert fn
    assert fn.function_name
    assert fn.runtime.name == "python3.8"

def test_make_lambda_python_function():
    stack = ATestStack()
    resource = {
        "name": "trigger_fn",
        "type": "lambda_function",
        "config": {
            "entry": "tests/customcode/lambda_functions/example_1_fx",
            "index": "example_handler.py",
            "handler": "handler",
            "runtime": "python3.8",
        },
    }
    fn, _ = resource_task.make_lambda_python_function(stack, resource)
    assert fn
    assert fn.function_name
    assert fn.runtime.name == "python3.8"


def test_make_lambda_python_function_with_layer():
    stack = ATestStack()
    resource = {
        "name": "trigger_fn",
        "type": "lambda_function",
        "config": {
            "entry": "tests/customcode/lambda_functions/example_1_fx",
            "index": "example_handler.py",
            "handler": "handler",
            "runtime": "python3.8",
            "layer_ref": ["pandas"],
        },
    }
    cmd = """rm -rf /asset-output/python  &&
                    pip install -r requirements.txt --target /asset-output/python  &&
                    rm -rf /asset-output/python/scipy* && rm -rf /asset-output/python/numpy*
          """
    stack.layer_versions["pandas"] = resource_task.make_lambda_layer(
        stack, "pandas", "customcode/lambda_layers/pandas", resource_task.lambda_to_runtime({"config": {"runtime": "python3.8"}}), cmd
    )

    fn, ev = resource_task.make_lambda_python_function(stack, resource)
    assert fn
    assert not ev


def test_make_lambda_python_function_with_schedule():
    stack = ATestStack()
    resource = {
        "name": "trigger_fn",
        "type": "lambda_function",
        "config": {
            "entry": "tests/customcode/lambda_functions/example_1_fx",
            "index": "example_handler.py",
            "handler": "handler",
            "runtime": "python3.8",
            "scheduler": {"cron": "cron(0 4 * * ? *)"},
        },
    }
    fn, events = resource_task.make_lambda_python_function(stack, resource)

    assert fn
    assert events
    assert stack.tags_tracker[fn] == stack.resource_tags


def test_make_lambda_python_function_with_multiple_schedules():
    stack = ATestStack()
    resource = {
        "name": "trigger_fn",
        "type": "lambda_function",
        "config": {
            "entry": "tests/customcode/lambda_functions/example_1_fx",
            "index": "example_handler.py",
            "handler": "handler",
            "runtime": "python3.8",
            "schedulers": [ {"cron": "cron(0 4 * * ? *)",
                             "payload": "{ 'site_id': 4}"
                            },
                            {"cron": "cron(0 4 * * ? *)",
                             "payload": "{ 'site_id': 5}"
                            }]
        }
    }
    fn, events = resource_task.make_lambda_python_function(stack, resource)

    assert fn
    assert events
    assert stack.tags_tracker[fn] == stack.resource_tags

def test_make_layer_version():
    stack = ATestStack()
    resource = {
        "config": {"bundle_type": "simple", "layer_entry": "customcode/lambda_layers/awswrangler", "runtime": "python3.8"},
        "name": "awswrangler",
    }
    resource_task.make_lambda_layer_version(stack, resource)
    assert stack.layer_versions["awswrangler"]

    resource = {
        "config": {"layer_entry": "customcode/lambda_layers/awswrangler", "runtime": "python3.8", "description": "AWS Wrangler layer"},
        "name": "awswrangler_2",
    }
    resource_task.make_lambda_layer_version(stack, resource)
    assert stack.layer_versions["awswrangler_2"]


def test_make_layer_version_fails():
    stack = ATestStack()

    resource = {
        "name": "trigger_fn",
        "type": "lambda_function",
        "config": {
            "entry": "tests/customcode/lambda_functions/example_1_fx",
            "index": "example_handler.py",
            "handler": "handler",
            "runtime": "python3.8",
            "scheduler": {"cron": "invalid cron"},
        },
    }

    invalid_scheduler = False
    try:
        resource_task.make_lambda_python_function(stack, resource)
    except resource_task.ResourceCreationException as e:
        assert "lambda" in str(e)
        invalid_scheduler = True

    resource = {
        "config": {
            "bundle_type": "complete",
            "layer_entry": "customcode/lambda_layers/awswrangler",
            "runtime": "python3.8",
        },
        "name": "awswrangler",
    }

    invalid_bundle = False
    try:
        resource_task.make_lambda_layer_version(stack, resource)
    except resource_task.ResourceCreationException as e:
        assert "(layerversion)" in str(e)
        invalid_bundle = True

    resource = {"config": {"bundle_type": "complete", "runtime": "python3.8"}, "name": "awswrangler"}
    missing_input = False
    try:
        resource_task.make_lambda_layer_version(stack, resource)
    except resource_task.ResourceCreationException as e:
        assert "(layerversion)" in str(e)
        missing_input = True

    print(invalid_scheduler, invalid_bundle, missing_input)
    assert invalid_scheduler and invalid_bundle and missing_input
