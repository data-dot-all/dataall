import json

import pytest
from aws_cdk import App

from dataall.cdkproxy.stacks import EnvironmentSetup
from dataall.cdkproxy.stacks.environment import EnvironmentStackExtension

from dataall.modules.mlstudio.cdk.mlstudio_stack import SagemakerStudioUserProfile


@pytest.fixture(scope='function', autouse=True)
def patch_methods(mocker, db, sgm_studio, env, org):
    mocker.patch(
        'dataall.modules.mlstudio.cdk.mlstudio_stack.SagemakerStudioUserProfile.get_engine',
        return_value=db,
    )
    mocker.patch(
        'dataall.aws.handlers.sts.SessionHelper.get_delegation_role_name',
        return_value="dataall-pivot-role-name-pytest",
    )
    mocker.patch(
        'dataall.modules.mlstudio.cdk.mlstudio_stack.SagemakerStudioUserProfile.get_target',
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


@pytest.fixture(scope='function', autouse=True)
def patch_methods_sagemaker_studio_extension(mocker):
    mocker.patch(
        'dataall.aws.handlers.sts.SessionHelper.get_cdk_look_up_role_arn',
        return_value="arn:aws:iam::1111111111:role/cdk-hnb659fds-lookup-role-1111111111-eu-west-1",
    )
    mocker.patch(
        'dataall.modules.mlstudio.aws.ec2_client.EC2.check_default_vpc_exists',
        return_value=False,
    )
    #TODO = WAYS OF TESTING EXTENSIONS
