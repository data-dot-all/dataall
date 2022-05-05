"""
Helper file to dataallPipeline stack operations: creation of sql_queries, tasks.
"""
import re
import textwrap

from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk.aws_lambda import Code
from aws_cdk.aws_stepfunctions import Choice, Condition, Pass
from engine import (SageMakerImageBuilder, make_athena_query_task,
                    make_batch_task, make_glue_job_task,
                    make_lambda_function_task, make_publish_to_sns_task,
                    make_sagemaker_batch_transform_task,
                    make_sagemaker_endpoint_config_task,
                    make_sagemaker_endpoint_task, make_sagemaker_hpo_task,
                    make_sagemaker_model_task, make_sagemaker_processing_task,
                    make_sagemaker_training_task)


class PipelineTaskException(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = f'Failed to create pipeline due to {message}'

    def __str__(self):
        return self.message


## Methods to build the step function and the sql_queries


def make_step_function_task(stack, job, group_index=-1, job_index=-1):
    """Make a task of step functions.
    It can be either
        - glue_job, for glue job
        - athena_query, for athena query
        - sns_publish, for publishing to SNS topic
        - lambda_function, for creation of lambdafx function
        - batch, for AWS batch job
        - sagemaker_training, for Sage maker training
        - sagemaker_hpo, for hyperparameter optimization using sagemaker
        - sagemaker_processing, for sagemaker processing
        - sagemaker_model, for creation of a sage maker model
        - sagemaker_endpoint_config, for creation of an endpoint configuration
        - sagemaker_endpoint, for creation of end point
        - choice, for a simple, typically runtime branching.
    Parameters
        job: the configuration of the job.
    """

    if job.get('type') == 'glue_job':
        task = make_glue_job_task(
            stack, job, stage=stack.stage, bucket_name=stack.bucket_name
        )
    elif job.get('type') == 'sagemaker_training':
        task = make_sagemaker_training_task(stack, job, group_index, job_index)
    elif job.get('type') == 'sagemaker_hpo':
        task = make_sagemaker_hpo_task(stack, job, group_index, job_index)
    elif job.get('type') == 'sagemaker_processing':
        task = make_sagemaker_processing_task(stack, job, group_index, job_index)
    elif job.get('type') == 'sagemaker_model':
        task = make_sagemaker_model_task(stack, job, group_index, job_index)
    elif job.get('type') == 'sagemaker_endpoint_config':
        task = make_sagemaker_endpoint_config_task(stack, job, group_index, job_index)
    elif job.get('type') == 'sagemaker_endpoint':
        task = make_sagemaker_endpoint_task(stack, job, group_index, job_index)
    elif job.get('type') == 'lambda_function':
        task = make_lambda_function_task(stack, job)
    elif job.get('type') == 'sagemaker_batch_transform':
        task = make_sagemaker_batch_transform_task(stack, job)
    elif job.get('type') == 'athena_query':
        task = make_athena_query_task(stack, job)
    elif job.get('type') == 'sns_publish':
        task = make_publish_to_sns_task(stack, job)
    elif job.get('type') == 'batch':
        task = make_batch_task(stack, job)
    elif job.get('type') == 'choice':
        task = make_choice_task(stack, job)
    elif job.get('type') == 'fail':
        task = stepfunctions.Fail(
            stack,
            f"Fail: {job['name']}",
            cause=job.get('config').get('cause', ''),
            comment=job.get('config').get('comment', ''),
            error=job.get('config').get('error', ''),
        )
    elif job.get('type') == 'succeed':
        task = stepfunctions.Succeed(
            stack,
            f"Succeed: {job['name']}",
            comment=job.get('config').get('comment', ''),
            input_path=job.get('config').get('input_path', '$'),
            output_path=job.get('config').get('output_path', '$'),
        )
    else:
        raise PipelineTaskException(f"Unknown job type {job.get('type')}")
    return task


def append_step_function_parallels(stack, parallels, task_list, group, name):
    """Update the parallels by appending a task list.

    All jobs defined in the same group are going to be executed in a step function parallel.
    If there is only one, then it uses a simple task instead.

    Parameters
        parallels: sequence of parallels (or task)
        task_list : a list of job
        group: the current group configuration

    """
    if name:
        name = group.get('name') + '_' + name
    else:
        name = group.get('name')
    if len(task_list) == 1:
        parallels.append(task_list[0])
    else:
        parallel = stepfunctions.Parallel(
            stack,
            name,
            result_path=stepfunctions.JsonPath.DISCARD,
            comment=group.get('comment'),
        )
        for task in task_list:
            parallel.branch(task)

        parallels.append(parallel)


def build_step_function_definition_uncompiled(stack, pipeline_definition):
    parallels = []
    for group_index, group in enumerate(pipeline_definition.get('groups')):
        task_list = []

        # Make all jobs in the same groups to be in a step function parallel.
        for job_index, job in enumerate(group.get('jobs')):
            task = stack.make_step_function_task(job, group_index, job_index)

            if isinstance(task, list) and job.get('type') != 'choice':
                # Currently this step is used for nested Athena config files
                # but notice that it can be re-used for other engines
                # [[task1,task2],[task3,task4]]
                index = 1
                step_parallels = []
                for index, step_task_list in enumerate(task):
                    # one step: [task1, task2]
                    name = job.get('name') + '_' + str(index)
                    append_step_function_parallels(
                        stack, step_parallels, step_task_list, group, name
                    )
                    index = index + 1

                subdefinition, first, last = compile_step_function_definition(
                    step_parallels,
                    job_name_generator_task=None,
                    use_name_generator_task=None,
                )
                task_list.append(subdefinition)
            else:
                task_list.append(task)

        append_step_function_parallels(stack, parallels, task_list, group, name=None)
    return parallels


def compile_step_function_definition(
    parallels, job_name_generator_task, use_name_generator_task
):
    """Compiles a definition of state machine given the structure of groups.
        It receives a structure of parallels that comes mainly from group blocks in the configuration file.
        The function links together the tasks and define the next of each task.

    Parameters
        parallels: the parsed structure of the state machine. It consists of sequence of parallel candidates.
    """
    definition = (
        job_name_generator_task
        if (job_name_generator_task and use_name_generator_task)
        else parallels[0]
    )
    i = 0 if (job_name_generator_task and use_name_generator_task) else 1
    last_branch = None
    if len(parallels) >= 1:
        prev_parallel = None
        for parallel in parallels[i:]:
            if isinstance(prev_parallel, list):
                for p in prev_parallel[1]:
                    p.next(parallel)
                last_branch = parallel
            else:
                if isinstance(parallel, list):
                    if last_branch:
                        last_branch = last_branch.next(parallel[0])
                    else:
                        definition = definition.next(parallel[0])
                else:
                    if last_branch:
                        last_branch = last_branch.next(parallel)
                    else:
                        definition = definition.next(parallel)

            prev_parallel = parallel

    first = parallels[0][0] if isinstance(parallels[0], list) else parallels[0]
    last = parallels[-1][1][0] if isinstance(parallels[-1], list) else parallels[-1]
    return definition, first, last


def build_step_function_definition(
    stack, pipeline_definition, job_name_generator_task, use_name_generator_task
):
    """Make sequence of parallels from groups
    Parameters
        stack
        pipeline_definition
        job_name_generator_task: output of create_glue_job_names_with_execution_id
        use_name_generator_task: True/False
    """
    parallels = build_step_function_definition_uncompiled(stack, pipeline_definition)
    definition = compile_step_function_definition(
        parallels, job_name_generator_task, use_name_generator_task
    )
    print(f'Definition:{definition}')
    return definition


## Additional methods


def make_choice_task(stack, job):
    task = Choice(stack, f"Branch: {job['name']}")
    pass_task = Pass(stack, 'Pass' + job['name'])

    for i, choice_config in enumerate(job['choices']):
        condition_type, value = list(choice_config['condition'].items())[0]
        sub_job = choice_config.copy()

        target_task, first_state, next_state = build_step_function_definition(
            stack, sub_job, None, False
        )
        if condition_type == 'BooleanEquals':
            # replace with input
            task = task.when(
                Condition.boolean_equals(choice_config['input'], value),
                first_state,
            )
        elif condition_type == 'StringEquals':
            task = task.when(
                Condition.string_equals(choice_config['input'], value),
                first_state,
            )
        else:
            raise Exception(
                'Unknown condition {} at choice task'.format(condition_type)
            )
        next_state.next(pass_task)
    task.otherwise(pass_task)
    return [task, [pass_task]]


def build_sagemaker_training_processing_job_image(self, groups):
    """Builds sagemaker processing job images.
    The build only happens when the there are glue_jobs whose job type is either processing or training.

    Parameters
        groups: the definition of the groups from configuration file.
    """
    all_types = [job['type'] for group in groups for job in group['jobs']]

    token = None
    if ('processing' in all_types) or ('training' not in all_types):
        token = SageMakerImageBuilder.connect_to_ecr(self.pipeline_region)
        SageMakerImageBuilder.build_processing_job_image(self.ecr_repository_uri, token)
    else:
        print('Skip build processing job image')

    return token


def create_glue_job_names_with_execution_id(self, pipeline, job_names):
    """Creates the glue jobs with execution ID
    Parameters
        pipeline: parsed configuration file
        job_names: names of the jobs defined in the config.yaml
    """
    for j, group in enumerate(pipeline.definition.get('groups', [])):
        for i, job in enumerate(group.get('jobs')):
            job_name = re.sub(r'[^a-zA-Z0-9-]', '', job.get('name')).lower()
            job_names.append(
                {
                    'index': f'{j}|{i}',
                    'type': f"{job['type']}",
                    'job_name': job_name,
                }
            )

    if any(job['type'] != 'glue_job' for job in job_names):
        job_name_generator = lambda_.Function(
            self,
            'jobIdGenerator',
            code=Code.from_inline(
                textwrap.dedent(
                    """
                    from datetime import datetime
                    def handler(event, context):
                        print("received event --->", event)
                        job_names = {}
                        for i, j in enumerate(event["jobs"]):
                            job_names[j["index"]] = f"{j['job_name']}-{event['execution_id']}"
                            if j["type"] == "hpo":
                                job_names[j["index"]] = f"{j['job_name'][:24]}-{event['execution_id'][:7]}"
                            else:
                                job_names[j["index"]] = f"{j['job_name'][:32]}-{event['execution_id']}"

                        job_names["tags"] = event["tags"]
                        job_names["tags"].append({"Key": "ExecutionID", "Value": event['execution_id']})
                        return job_names
                """
                )
            ),
            handler='index.handler',
            runtime=lambda_.Runtime.PYTHON_3_7,
            memory_size=3008,
        )
        tags = [{'Key': k, 'Value': v} for k, v in self.resource_tags.items()]
        job_name_generator_task = tasks.LambdaInvoke(
            self,
            'Task Execution Id',
            lambda_function=job_name_generator,
            payload=stepfunctions.TaskInput.from_object(
                {
                    'jobs': job_names,
                    'tags': tags,
                    'execution_id': stepfunctions.TaskInput.from_data_at(
                        '$$.Execution.Name'
                    ).value,
                }
            ),
            payload_response_only=True,
            result_path='$.job_names',
        )
        return job_name_generator_task
