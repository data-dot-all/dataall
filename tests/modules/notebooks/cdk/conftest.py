import pytest

from dataall.modules.notebooks.models import SagemakerNotebook
from dataall.db import models
from tests.cdkproxy.conftest import org, env


@pytest.fixture(scope='module', autouse=True)
def stack_org(db) -> models.Organization:
    yield org


@pytest.fixture(scope='module', autouse=True)
def stack_env(db, stack_org: models.Organization) -> models.Environment:
    yield env


@pytest.fixture(scope='module', autouse=True)
def notebook(db, env: models.Environment) -> SagemakerNotebook:
    with db.scoped_session() as session:
        notebook = SagemakerNotebook(
            label='thistable',
            NotebookInstanceStatus='RUNNING',
            owner='me',
            AWSAccountId=env.AwsAccountId,
            region=env.region,
            environmentUri=env.environmentUri,
            RoleArn=env.EnvironmentDefaultIAMRoleArn,
            SamlAdminGroupName='admins',
            VolumeSizeInGB=32,
            InstanceType='ml.t3.medium',
        )
        session.add(notebook)
    yield notebook
