import json

import pytest
from aws_cdk import App

from dataall.cdkproxy.stacks import SagemakerNotebook


@pytest.fixture(scope='function', autouse=True)
def patch_methods(mocker, db, notebook, env, org):
    mocker.patch(
        'dataall.cdkproxy.stacks.notebook.SagemakerNotebook.get_engine',
        return_value=db,
    )
    mocker.patch(
        'dataall.aws.handlers.sts.SessionHelper.get_delegation_role_name',
        return_value="dataall-pivot-role-name-pytest",
    )
    mocker.patch(
        'dataall.cdkproxy.stacks.notebook.SagemakerNotebook.get_target',
        return_value=notebook,
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_engine', return_value=db
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_target',
        return_value=notebook,
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_environment',
        return_value=env,
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_organization',
        return_value=org,
    )


@pytest.fixture(scope='function', autouse=True)
def template(notebook):
    app = App()
    SagemakerNotebook(app, 'SagemakerNotebook', target_uri=notebook.notebookUri)
    return json.dumps(app.synth().get_stack_by_name('SagemakerNotebook').template)


def test_resources_created(template):
    assert 'AWS::SageMaker::NotebookInstance' in template
