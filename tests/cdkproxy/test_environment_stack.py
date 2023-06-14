import json

import pytest
from aws_cdk import App, Stack
from aws_cdk.assertions import Template

from dataall.cdkproxy.stacks import EnvironmentSetup


@pytest.fixture(scope='function', autouse=True)
def patch_extensions(mocker):
    for extension in EnvironmentSetup._EXTENSIONS:
        mocker.patch(
            f"{extension.__module__}.{extension.__name__}.extent",
            return_value=True,
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
        return_value='secretIdvalue',
    )


def test_resources_created(env, org):
    app = App()

    # Create the Stack
    stack = EnvironmentSetup(app, 'Environment', target_uri=env.environmentUri)

    # Prepare the stack for assertions.
    template = Template.from_stack(stack)

    # Assert that we have created:
    # TODO: Add more assertions
    template.resource_properties_count_is(
        type="AWS::S3::Bucket",
        props={
            'BucketName': env.EnvironmentDefaultBucketName,
            'BucketEncryption': {
                'ServerSideEncryptionConfiguration': [{
                    'ServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}
                }]
            },
            'PublicAccessBlockConfiguration': {
                'BlockPublicAcls': True,
                'BlockPublicPolicy': True,
                'IgnorePublicAcls': True,
                'RestrictPublicBuckets': True
            },
            'Tags': [
                {'Key': 'CREATOR', 'Value': 'customtagowner'},
                {'Key': 'dataall', 'Value': 'true'},
                {'Key': 'Environment', 'Value': f'env_{env.environmentUri}'},
                {'Key': 'Organization', 'Value': f'org_{org.organizationUri}'},
                {'Key': 'Target', 'Value': f'Environment_{env.environmentUri}'},
                {'Key': 'Team', 'Value': env.SamlGroupName}],
        },
        count=1
    )
    template.resource_count_is("AWS::S3::Bucket", 1)
    template.resource_count_is("AWS::Lambda::Function", 7)
    template.resource_count_is("AWS::SSM::Parameter", 10)
    template.resource_count_is("AWS::IAM::Role", 5)
    template.resource_count_is("AWS::IAM::Policy", 4)


