from aws_cdk import aws_stepfunctions
from aws_cdk import aws_iam
from aws_cdk import aws_ssm

import uuid
import logging
import re
import structlog

lg = logging.getLogger()
lg.setLevel(logging.INFO)
logger = structlog.wrap_logger(lg, processors=[structlog.processors.JSONRenderer()])


def _job_queue_arn_from_ref(stack, job_queue_ref):
    """Obtains arn of a job queue defined in AWS resources.
    :param stack the dataall pipeline stack
    :param job_queue_ref the pointer to a JobQueue object.
    :return the ARN of the job queue.
    """
    return (
        stack.resources.get(job_queue_ref).job_queue_arn
        if job_queue_ref in stack.resources
        else None
    )


def _job_definition_arn_from_ref(stack, job_definition_ref):
    """OBtains arn of a job definition defined in AWS resources block.
    :param stack the dataall pipeline stack
    :param job_definition_ref the pointer to a JobDefinition object.
    :return the ARN of the job definition.
    """
    return stack.resources.get(job_definition_ref).job_definition_arn


def _map_container_overrides(stack, cfg):
    """Maps container overrides part of configuration from a configuration dictionary.
    Container overrides provides a way to redefine command, environment variable, number of GPUs, instance type, memory size, and
    number of VCPUs.

    Examples:
        Example 1:
            container_overrides:
                command:
                   - b
                   - dhcatsx5t7deuwest1
                   - -o
                   - cats
                   - -d
                   - transformed_cats
                   - --height
                   - "120"
                   - --width
                   - "210"
                environment:
                    host: myhost
                    port: 1521

                memory_size: 2048
                vcpus: 4
        Example 2: Using input from parameter
            container_overrides:
                command_from_path: $.batch_command
                environment: $.batch_environment_variables
                memory_size: 2048
                vcpus: 4

        Example 3: You can also define command and environment directly outside container_overrides block.
                command:
                   - b
                   - dhcatsx5t7deuwest1
                   - -o
                   - cats
                   - -d
                   - transformed_cats
                   - --height
                   - "120"
                   - --width
                   - "210"
                environment:
                    host: myhosts
                    port: 1521

    :param stack the dataall pipeline stack.
    :param cfg the configuration dictionary corresponding to configuration part of a container override.
    :return container_overrides configuration can be used for CDK.
    """

    container_overrides = cfg.get('container_overrides', {})

    command = container_overrides.get('command')
    command_from_path = container_overrides.get('command_from_path')

    environment_variables = container_overrides.get('environment')
    environment_from_path = container_overrides.get('environment_from_path')

    gpu_count = container_overrides.get('gpu_count')
    gpu_count_from_path = container_overrides.get('gpu_count_from_path')

    instance_type = container_overrides.get('instance_type')
    instance_type_from_path = container_overrides.get('instance_type_from_path')

    memory_size = container_overrides.get('memory_size')
    memory_size_from_path = container_overrides.get('memory_size_from_path')

    vcpus = container_overrides.get('vcpus')
    vcpus_from_path = container_overrides.get('vcpus_from_path')

    if not (command or command_from_path):
        # Get from the root
        command = cfg.get('command')
        command_from_path = cfg.get('command_from_path')

    if (container_overrides or command or command_from_path) and (
        command
        or command_from_path
        or environment_variables
        or environment_from_path
        or gpu_count
        or gpu_count_from_path
        or instance_type
        or instance_type_from_path
        or memory_size
        or memory_size_from_path
        or vcpus
        or vcpus_from_path
    ):
        bco = {}
        if command:
            bco['Command'] = command
        if command_from_path:
            bco['Command.$'] = command_from_path
        if environment_variables:
            bco['Environment'] = environment_variables
        if environment_from_path:
            bco['Environment.$'] = environment_from_path
        if (
            gpu_count
            or gpu_count_from_path
            or memory_size
            or memory_size_from_path
            or vcpus
            or vcpus_from_path
        ):
            resource_req = []
            if gpu_count:
                resource_req.append({'Type': 'GPU', 'Value': gpu_count})
            if gpu_count_from_path:
                resource_req.append({'Type': 'GPU', 'Value.$': gpu_count_from_path})

            if memory_size:
                resource_req.append({'Type': 'MEMORY', 'Value': memory_size})
            if memory_size_from_path:
                resource_req.append(
                    {'Type': 'MEMORY', 'Value.$': memory_size_from_path}
                )

            if vcpus:
                resource_req.append({'Type': 'VCPU', 'Value': vcpus})
            if vcpus_from_path:
                resource_req.append({'Type': 'VCPU', 'Value.$': vcpus_from_path})
            bco['ResourceRequirements'] = resource_req

        if instance_type:
            bco['InstanceType'] = instance_type
        if instance_type_from_path:
            bco['InstanceType.$'] = instance_type_from_path
        return bco
    else:
        return None


def _map_job_queue(stack, job):
    """Resolves job queue. You can refer to a job queue in the following ways:
    1. Direct reference of job_queue defined in the same config.yaml file.
    2. Job_queue ARN directly or from step function path.
    3. Job_queue ARN defined in an SSM.

    :param stack the dataall data pipeline stack
    :job the job configuration
    :return the job queue part of the job configuration
    """
    job_queue_ref = job.get('job_queue_ref')

    if 'job_queue_param' in job:
        job_queue_param = aws_ssm.StringParameter.from_string_parameter_name(
            stack, 'JobQueueParam', string_parameter_name=job.get('job_queue_param')
        ).string_value
    else:
        job_queue_param = None

    job_queue_arn_from_path = job.get('job_queue_arn_from_path')
    if job_queue_arn_from_path and job_queue_arn_from_path[:2] != '$.':
        raise Exception('From path must start with $.')

    job_queue_arn = (
        job.get('job_queue_arn') or job_queue_arn_from_path or job_queue_param
    )

    return (
        job_queue_arn
        if job_queue_arn
        else _job_queue_arn_from_ref(stack, job_queue_ref)
    )


def _map_job_definition(stack, job):
    """Resolves job definition. You can refer to a job definition in the following ways:
    1. Direct reference of job_Definition defined in the same config.yaml file.
    2. Job_definition ARN directly or from step function path.
    3. Job_definition ARN defined in an SSM.

    :param stack the dataall data pipeline stack
    :job the job configuration
    :return the job definition part of the job configuration
    """

    job_definition_ref = job.get('job_definition_ref')

    if 'job_definition_param' in job:
        job_definition_param = aws_ssm.StringParameter.from_string_parameter_name(
            stack,
            'JobDefinitionARN',
            string_parameter_name=job.get('job_definition_param'),
        ).string_value
    else:
        job_definition_param = None

    job_definition_arn_from_path = job.get('job_definition_arn_from_path')
    if job_definition_arn_from_path and job_definition_arn_from_path[:2] != '$.':
        raise Exception('From path must start with $.')

    job_definition_arn = (
        job.get('job_definition_arn')
        or job_definition_arn_from_path
        or job_definition_param
    )
    return (
        job_definition_arn
        if job_definition_arn
        else _job_definition_arn_from_ref(stack, job_definition_ref)
    )


def _make_batch_job_task_definition(stack, job, job_name):
    """Submits batch job.
    The caller can provide the job queue and job definition arns from input, or define them in the aws_resources block,
    and then reference it from here.

    :param stack the enclosing stack
    :job the configuration.
    :job_name the sanitized job name
    """
    cfg = job.get('config')
    timeout = cfg.get('timeout', 3600)
    parameters = {'Timeout': {'AttemptDurationSeconds': timeout}}

    array_size = cfg.get('array_size')

    parameters['ContainerOverrides'] = _map_container_overrides(
        stack, cfg.get('container_overrides', {})
    )

    jobdef = _map_job_definition(stack, job)
    if jobdef[:2] == '$.':
        parameters['JobDefinition.$'] = jobdef
    else:
        parameters['JobDefinition'] = jobdef

    jobq = _map_job_queue(stack, job)
    if jobq[:2] == '$.':
        parameters['JobQueue.$'] = jobq
    else:
        parameters['JobQueue'] = jobq

    depends_on = cfg.get('depends_on')
    propagate_tags = cfg.get('propagate_tags')

    if depends_on:
        parameters['DependsOn'] = depends_on

    params = cfg.get('parameters')
    if params:
        parameters['Parameters'] = params

    if propagate_tags:
        parameters['PropagateTags'] = propagate_tags

    attempts = job.get('attempts', 1)
    if array_size:
        parameters['ArrayProperties'] = {'Size': array_size}
    if attempts:
        parameters['RetryStrategy'] = {'Attempts': attempts}

    parameters['JobName'] = job_name

    return {
        'Type': 'Task',
        'Resource': 'arn:aws:states:::batch:submitJob.sync',
        'Parameters': parameters,
    }


def deploy_submit_batch_job(stack, job):

    sanitized_job_name = sanitized_name(job['name'])

    definition = _make_batch_job_task_definition(stack, job, sanitized_job_name)

    input_path = job.get('input_path', '$')
    output_path = job.get('output_path', '$')
    result_path = job.get('result_path')

    definition['InputPath'] = input_path
    if result_path:
        definition['ResultPath'] = result_path
    definition['OutputPath'] = output_path

    retry_definition = job.get('retry')

    if retry_definition:
        definition['Retry'] = [
            {
                'IntervalSeconds': retry_definition.get('interval_seconds', 1),
                'MaxAttempts': retry_definition.get('retry_attempt', 3),
                'BackoffRate': retry_definition.get('backoff_rate', 1.1),
            }
        ]

    return aws_stepfunctions.CustomState(
        stack,
        id=f'batch-{sanitized_job_name}',
        state_json=definition,
    )


def sanitized_name(name):
    return re.sub(r'[^a-zA-Z0-9-]', '', name).lower()


def map_role(stack, batch_name, config_props):
    """Defines the role to be used by the batch job function. The role must be defined under 'role' section
    of config, for example:
    When not defined, the environment role is used.

    Parameters
        stack the pipeline stack
        batch_name the function name to be used to create the role.
        config_props the configuration of the lambda.
    """
    return aws_iam.Role.from_role_arn(
        stack,
        f'{batch_name}Role-{str(uuid.uuid4())[:8]}',
        config_props.get('role', stack.pipeline_iam_role_arn),
        mutable=False,
    )


def make_batch_task(stack, job):
    """Submits a batch task given a job queue ARN.
    The job queue may be defined in aws_resource block or provided
    as an
    """
    logger.info('make_batch_task', job=job)

    return deploy_submit_batch_job(stack, job)
