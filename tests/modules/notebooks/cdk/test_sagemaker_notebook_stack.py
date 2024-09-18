import json
import os
import pytest
from aws_cdk import App

from dataall.modules.notebooks.cdk.notebook_stack import NotebookStack
from tests.skip_conditions import checkov_scan


@pytest.fixture(scope='function', autouse=True)
def patch_methods(mocker, db, notebook, env_fixture, org_fixture):
    mocker.patch('dataall.modules.notebooks.cdk.notebook_stack.NotebookStack.get_engine', return_value=db)
    mocker.patch(
        'dataall.base.aws.sts.SessionHelper.get_delegation_role_name',
        return_value='dataall-pivot-role-name-pytest',
    )
    mocker.patch(
        'dataall.modules.notebooks.cdk.notebook_stack.NotebookStack.get_target',
        return_value=notebook,
    )
    mocker.patch('dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_engine', return_value=db)
    mocker.patch(
        'dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_target',
        return_value=notebook,
    )
    mocker.patch(
        'dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_environment',
        return_value=env_fixture,
    )
    mocker.patch(
        'dataall.core.stacks.services.runtime_stacks_tagging.TagsUtil.get_organization',
        return_value=org_fixture,
    )


@pytest.fixture(scope='function', autouse=True)
def template(notebook):
    app = App()
    NotebookStack(app, 'SagemakerNotebook', target_uri=notebook.notebookUri)
    return json.dumps(app.synth().get_stack_by_name('SagemakerNotebook').template)


def test_resources_created(template):
    assert 'AWS::SageMaker::NotebookInstance' in template


@checkov_scan
def test_checkov(template):
    with open('checkov_notebook_synth.json', 'w') as f:
        f.write(template)
