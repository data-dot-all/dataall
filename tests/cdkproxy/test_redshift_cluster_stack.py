import json

import pytest
from aws_cdk import App

from dataall.cdkproxy.stacks import RedshiftStack


@pytest.fixture(scope="function", autouse=True)
def patch_methods(mocker, db, redshift_cluster, env, org):
    mocker.patch(
        "dataall.cdkproxy.stacks.redshift_cluster.RedshiftStack.get_engine",
        return_value=db,
    )
    mocker.patch(
        "dataall.aws.handlers.sts.SessionHelper.get_delegation_role_name",
        return_value="dataall-pivot-role-name-pytest",
    )
    mocker.patch(
        "dataall.cdkproxy.stacks.redshift_cluster.RedshiftStack.get_target",
        return_value=(redshift_cluster, env),
    )
    mocker.patch("dataall.utils.runtime_stacks_tagging.TagsUtil.get_engine", return_value=db)
    mocker.patch(
        "dataall.utils.runtime_stacks_tagging.TagsUtil.get_target",
        return_value=redshift_cluster,
    )
    mocker.patch(
        "dataall.utils.runtime_stacks_tagging.TagsUtil.get_environment",
        return_value=env,
    )
    mocker.patch(
        "dataall.utils.runtime_stacks_tagging.TagsUtil.get_organization",
        return_value=org,
    )


@pytest.fixture(scope="function", autouse=True)
def template(redshift_cluster):
    app = App()
    RedshiftStack(
        app,
        "Cluster",
        env={"account": "123456789012", "region": "eu-west-1"},
        target_uri=redshift_cluster.clusterUri,
    )
    return json.dumps(app.synth().get_stack_by_name("Cluster").template)


def test_resources_created(template):
    assert "AWS::Redshift::Cluster" in template
    assert "AWS::SecretsManager::Secret" in template
    assert "AWS::KMS::Key" in template
