from aws_cdk import aws_stepfunctions_tasks as tasks
from .athena_config_reader import AthenaConfigReader
from aws_cdk import aws_stepfunctions as stepfunctions
import boto3

s3 = boto3.client('s3')


def read_query(query, workgroup):
    if query.startswith(
        'States.Format'
    ):  # For dynamic sql strings and prepared statements
        definition = {
            'Type': 'Task',
            'Resource': 'arn:aws:states:::athena:startQueryExecution.sync',
            'Parameters': {'QueryString.$': query, 'WorkGroup': workgroup},
        }

    elif isinstance(query, str):
        definition = {
            'Type': 'Task',
            'Resource': 'arn:aws:states:::athena:startQueryExecution.sync',
            'Parameters': {'QueryString': query, 'WorkGroup': workgroup},
        }
    else:
        logging.error('Unknown query type')

    return definition


def make_athena_query_task(stack, job):
    """Makes athena query task.
    It reads the sql statements uploaded to S3 from the main directory
    :param stack the enclosing step function stack
    :job the job configuration
    """
    # Define variables
    path = job.get('config').get('config_file')
    if job.get('config').get('variables'):
        variables = job.get('config').get('variables')
    else:
        variables = {}

    config = AthenaConfigReader(config_path=path, variables=variables)

    # Define Retry strategy
    if job.get('config').get('retry'):
        retry_definition = [
            {
                'ErrorEquals': job.get('config').get('retry').get('error_equals', []),
                'IntervalSeconds': job.get('config')
                .get('retry')
                .get('interval_seconds', 1),
                'MaxAttempts': job.get('config').get('retry').get('retry_attempt', 3),
                'BackoffRate': job.get('config').get('retry').get('backoff_rate', 1.1),
            }
        ]
    else:
        retry_definition = None

    # Define workgroup for athena query results
    # if None is given, it uses the environment group workgroup
    if job.get('config').get('workgroup'):
        workgroup = job.get('config').get('workgroup')
    else:
        ad_group = stack.pipeline_iam_role_arn.split('-')[-1]
        env_uri = stack.pipeline_iam_role_arn.split('/')[-2]
        workgroup = f'WG-{env_uri}-{ad_group}'

    # config.queries = [[query1,query2],[query3]...]
    step_task_list = []
    for step, query_list in zip(config.steps, config.queries):
        task_list = []
        for job, query in zip(step.get('jobs'), query_list):
            definition = read_query(query, workgroup)
            # Define Retry strategy
            if retry_definition != None:
                definition['Retry'] = retry_definition

            task = stepfunctions.CustomState(
                stack, 'Athena: ' + job['name'], state_json=definition
            )
            task_list.append(task)
        step_task_list.append(task_list)

    return step_task_list
