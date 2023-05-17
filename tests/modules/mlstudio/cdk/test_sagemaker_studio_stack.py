import json

import pytest
from aws_cdk import App

from dataall.modules.mlstudio.cdk.stacks import SagemakerStudioUserProfile


@pytest.fixture(scope='function', autouse=True)
def patch_methods(mocker, db, sgm_studio, env, org):
    mocker.patch(
        'dataall.modules.mlstudio.cdk.stacks.SagemakerStudioUserProfile.get_engine',
        return_value=db,
    )
    mocker.patch(
        'dataall.aws.handlers.sts.SessionHelper.get_delegation_role_name',
        return_value="dataall-pivot-role-name-pytest",
    )
    mocker.patch(
        'dataall.modules.mlstudio.cdk.stacks.SagemakerStudioUserProfile.get_target',
        return_value=sgm_studio,
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_engine', return_value=db
    )
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_target',
        return_value=sgm_studio,
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
def template(sgm_studio):
    app = App()
    SagemakerStudioUserProfile(
        app, 'Studio', target_uri=sgm_studio.sagemakerStudioUserUri
    )
    return json.dumps(app.synth().get_stack_by_name('Studio').template)


def test_resources_created(template):
    assert 'AWS::SageMaker::UserProfile' in template
