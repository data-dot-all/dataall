from aws_cdk.aws_lambda import Runtime

"""
Changing this will change the python runtime in:
* PROD Dockerfiles (lambda and ecs)
* Lambda runtimes
Will not change (so must manually be changed) in:
* dev/Dockerfile
"""
PYTHON_VERSION = '3.12'

PYTHON_LAMBDA_RUNTIME = getattr(Runtime, f'PYTHON_{PYTHON_VERSION.replace(".", "_")}')
