import json

import pytest
from aws_cdk import App

from dataall.cdkproxy.stacks import EnvironmentSetup

@pytest.fixture(scope='function', autouse=True)
def patch_methods_sagemaker_studio_extension(mocker):
    # TODO = WAYS OF TESTING EXTENSIONS outside of environment testing
    mocker.patch(
        'dataall.aws.handlers.sts.SessionHelper.get_cdk_look_up_role_arn',
        return_value="arn:aws:iam::1111111111:role/cdk-hnb659fds-lookup-role-1111111111-eu-west-1",
    )
    mocker.patch(
        'dataall.modules.mlstudio.aws.ec2_client.EC2.check_default_vpc_exists',
        return_value=False,
    )

@pytest.fixture(scope='function', autouse=True)
def patch_methods(mocker, db, env, another_group, permissions):
    mocker.patch(
        'dataall.cdkproxy.stacks.environment.EnvironmentSetup.get_engine',
        return_value=db,
    )
    mocker.patch(
        'dataall.aws.handlers.sts.SessionHelper.get_delegation_role_name',
        return_value='dataall-pivot-role-name-pytest',
    )
    mocker.patch(
        'dataall.aws.handlers.parameter_store.ParameterStoreManager.get_parameter_value',
        return_value='False',
    )
    mocker.patch(
        'dataall.cdkproxy.stacks.environment.EnvironmentSetup.get_target',
        return_value=env,
    )
    mocker.patch(
        'dataall.cdkproxy.stacks.environment.EnvironmentSetup.get_environment_groups',
        return_value=[another_group],
    )
    mocker.patch(
        'dataall.aws.handlers.sts.SessionHelper.get_account',
        return_value='012345678901x',
    )
    mocker.patch('dataall.utils.runtime_stacks_tagging.TagsUtil.get_engine', return_value=db)
    mocker.patch(
        'dataall.utils.runtime_stacks_tagging.TagsUtil.get_target',
        return_value=env,
    )
    mocker.patch(
        'dataall.cdkproxy.stacks.environment.EnvironmentSetup.get_environment_group_permissions',
        return_value=[permission.name for permission in permissions],
    )
    mocker.patch(
        'dataall.aws.handlers.sts.SessionHelper.get_external_id_secret',
        return_value='*****',
    )


@pytest.fixture(scope='function', autouse=True)
def template(env):
    app = App()
    EnvironmentSetup(app, 'Environment', target_uri=env.environmentUri)
    return json.dumps(app.synth().get_stack_by_name('Environment').template)


def test_resources_created(template, env):
    assert 'AWS::S3::Bucket' in template
    assert 'AWS::IAM::Role' in template
    assert 'AWS::Lambda::Function' in template
    assert 'AWS::IAM::Policy' in template
