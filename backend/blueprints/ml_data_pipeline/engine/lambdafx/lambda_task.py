from aws_cdk import aws_lambda_python as lambda_python
from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk import aws_iam as iam

from engine.lambdafx.lambda_mapper import LambdaFxPropsMapper
from engine import resource_task

""" Code where the lambdafx functions are created. It uses LambdaFxPropsMapper to build the parameters of Lambda functions
    and its invocations.
"""


def get_function_name(stack, job):
    """Creates a function name from the job name and the pipeline name.
    Truncates the pipeline name when necessary.
    Parameters
        stack: the containing stack
        job: the job configuration
    """
    if len(job['name']) > 38:
        raise Exception(
            'Name of the function cannot exceed 38 characters {}'.format(job['name'])
        )

    if len(job['name']) + len(stack.pipeline_name) >= 62:
        return f"{stack.pipeline_name[:20]}-{stack.pipeline_name[-4:]}-{job['name']}"
    else:
        return f"{stack.pipeline_name}-{job['name']}"


def default_lambda_description(job, stack):
    """Returns the default lambdafx description given the job name and pipeline name.
    Parameters
        job: the job definition
        stack: the stack englobing the lambdafx
    """
    return 'Python lambdafx created by data.all {} {}'.format(
        job['name'], stack.pipeline_name
    )


def make_lambda_function_task(stack, job):
    """Makes python function and its corresponding invocation.

    Parameters
        stack: the target CDK stack
        job: the job configuration
    """
    lambdafx = lambda_python.PythonFunction(
        stack,
        job['name'],
        runtime=resource_task.lambda_to_runtime(job),
        memory_size=job.get('memory_size', 1028),
        description=job.get('description', default_lambda_description(job, stack)),
        function_name=get_function_name(stack, job),
        **LambdaFxPropsMapper.map_function_props(stack, job['name'], job['config']),
    )

    # pipeline_iam_role_arn could access to the lambda
    principal = iam.ArnPrincipal(stack.pipeline_iam_role_arn)

    lambdafx.add_permission(
        f"LambdaPermissionBasic{job.get('name')}",
        principal=principal,
        action='lambda:*',
    )
    # pipeline_fulldev_iam_role could access to the lambda
    principal = iam.ArnPrincipal(stack.pipeline_fulldev_iam_role)

    lambdafx.add_permission(
        f"LambdaPermissionFullDev{job.get('name')}",
        principal=principal,
        action='lambda:*',
    )
    # pipeline_admin_iam_role could access to the lambda
    principal = iam.ArnPrincipal(stack.pipeline_admin_iam_role)

    lambdafx.add_permission(
        f"LambdaPermissionAdmin{job.get('name')}",
        principal=principal,
        action='lambda:*',
    )
    # Tag the lambdafx functions
    stack.set_resource_tags(lambdafx)

    # Make the invocation
    task = tasks.LambdaInvoke(
        stack,
        f"Lambda: {job.get('name')}",
        **LambdaFxPropsMapper.map_task_props(lambdafx, job['config']),
    )
    return task
