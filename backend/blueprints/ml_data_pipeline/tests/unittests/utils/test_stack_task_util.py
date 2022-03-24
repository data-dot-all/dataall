from utils.task_group_reader import TaskGroupReader
from aws_cdk import core
from utils import stack_task_util
import aws_cdk.aws_stepfunctions_tasks


class PipelineStack(core.Stack):
    def __init__(self, scope, pipeline, id, **kwargs):
        super().__init__(scope, f'dh-{id}', **kwargs)
        self.pipeline_name = 'pn'
        self.pipeline_iam_role_arn = (
            'arn:aws:iam::012345678912:role/dhdatasciencedevoqtnpj'
        )
        self.pipeline_fulldev_iam_role = (
            'arn:aws:iam::012345678901:role/dhdatasciencedevoqtnpj'
        )
        self.pipeline_admin_iam_role = (
            'arn:aws:iam::012345678901:role/dhdatasciencedevoqtnpj'
        )
        self.layer_versions = {}
        self.stage = 'test'
        self.bucket_name = 'irisclassification'
        self.jobdir = 'glue_jobs'
        self.resource_tags = {'Application': 'dataall'}
        self.pipeline_region = 'eu-west-1'
        self.tasks = []
        self.pipeline_definition = pipeline.definition
        for group in pipeline.definition.get('groups', []):
            for job in group.get('jobs', []):
                self.tasks.append(stack_task_util.make_step_function_task(self, job))

    def set_resource_tags(self, resource):
        pass

    def make_tag_str(self):
        pass


def test_make_step_function_task():
    pipeline = TaskGroupReader(
        path='tests/unittests/config_files/config_all_tasks.yaml'
    )
    stack = PipelineStack(None, pipeline, 'pipelinetest')

    assert isinstance(stack.tasks[0], aws_cdk.aws_stepfunctions_tasks.LambdaInvoke)
    assert isinstance(stack.tasks[1], aws_cdk.aws_stepfunctions_tasks.GlueStartJobRun)
    assert isinstance(stack.tasks[2], aws_cdk.aws_stepfunctions.Chain)

    hpo_job_name = pipeline.definition['groups'][2]['jobs'][0].get('name')
    assert stack.tasks[2].start_state.id == f'SageMaker HPO: {hpo_job_name}'
    assert stack.tasks[2].end_states[0].id == 'Lambda: get_best_model'

    assert isinstance(stack.tasks[3], aws_cdk.aws_stepfunctions.Chain)
    model_job_name = pipeline.definition['groups'][3]['jobs'][0].get('name')
    assert (
        stack.tasks[3].start_state.id
        == 'Lambda: Delete Model ' + model_job_name + ' If exists'
    )
    assert stack.tasks[3].end_states[0].id == 'Lambda: Tag Model ' + model_job_name

    assert isinstance(stack.tasks[4], aws_cdk.aws_stepfunctions.Chain)
    end_point_cfg_job_name = pipeline.definition['groups'][4]['jobs'][0].get('name')
    assert (
        stack.tasks[4].start_state.id
        == 'Lambda: Delete Endpoint Config ' + end_point_cfg_job_name + ' If exists'
    )
    assert (
        stack.tasks[4].end_states[0].id
        == 'Lambda: Tag Endpoint Config ' + end_point_cfg_job_name
    )

    assert isinstance(stack.tasks[5][0], aws_cdk.aws_stepfunctions.Chain)
    end_point_job_name = pipeline.definition['groups'][5]['jobs'][0].get('name')
    assert stack.tasks[5][0].id == 'Choice: Endpoint ' + end_point_job_name + ' Exists?'


def test_make_step_function_task_training():
    pipeline = TaskGroupReader(path='tests/unittests/config_files/config_training.yaml')
    stack = PipelineStack(None, pipeline, 'pipelinetest')

    assert isinstance(stack.tasks[0], aws_cdk.aws_stepfunctions_tasks.LambdaInvoke)
    assert (
        stack.tasks[0].id
        == f'Lambda: {pipeline.definition["groups"][0]["jobs"][0].get("name")}'
    )
    assert isinstance(stack.tasks[1], aws_cdk.aws_stepfunctions.CustomState)
    assert (
        stack.tasks[1].id
        == f'Task {pipeline.definition["groups"][1]["jobs"][0].get("name")}'
    )
    assert isinstance(stack.tasks[2], aws_cdk.aws_stepfunctions.Chain)
    assert (
        stack.tasks[2].id
        == f'Lambda: Tag Model {pipeline.definition["groups"][2]["jobs"][0].get("name")}'
    )
