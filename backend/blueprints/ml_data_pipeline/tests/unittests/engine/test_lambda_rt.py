from engine import resource_task
from aws_cdk import aws_lambda as lambda_


def test_to_runtime():
    # Test that by default Python 3.7 is the runtime.
    assert resource_task.lambda_to_runtime({"config": {}}).name == lambda_.Runtime.PYTHON_3_7.name
    assert resource_task.lambda_to_runtime({"config": {"runtime": "python3.6"}}).name == lambda_.Runtime.PYTHON_3_6.name
    assert resource_task.lambda_to_runtime({"config": {"runtime": "python3.8"}}).name == lambda_.Runtime.PYTHON_3_8.name
    assert resource_task.lambda_to_runtime({"config": {"runtime": "python3.7"}}).name == lambda_.Runtime.PYTHON_3_7.name

    # Tests case insensitiveness
    assert resource_task.lambda_to_runtime({"config": {"runtime": "pytHon3.6"}}).name == lambda_.Runtime.PYTHON_3_6.name

    # Tests raise exception
    failed = False
    try:
        resource_task.lambda_to_runtime({"config": {"runtime": "python2.7"}})
    except Exception as e:
        print(e)
        assert "python2.7" in e.message
        failed = True
    assert failed


def lambda_to_runtime(config):
    """Gets the runtime for python code.
    Parameter
        config: the configuration of the job/resource
    """
    rt = config["config"].get("runtime", "python3.7").lower()
    if rt == "python3.7":
        return lambda_.Runtime.PYTHON_3_7
    elif rt == "python3.6":
        return lambda_.Runtime.PYTHON_3_6
    elif rt == "python3.8":
        return lambda_.Runtime.PYTHON_3_8
    else:
        raise LambdaRuntimeException("Unsupported lambdafx runtime {}".format(rt))
