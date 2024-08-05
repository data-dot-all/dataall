import pytest

from dataall.core.environment.db.environment_models import Environment
from dataall.modules.notebooks.db.notebook_models import SagemakerNotebook


@pytest.fixture(scope='module', autouse=True)
def notebook(db, env_fixture: Environment) -> SagemakerNotebook:
    with db.scoped_session() as session:
        notebook = SagemakerNotebook(
            notebookUri='111111',
            label='thistable',
            NotebookInstanceStatus='RUNNING',
            owner='me',
            AWSAccountId=env_fixture.AwsAccountId,
            region=env_fixture.region,
            environmentUri=env_fixture.environmentUri,
            RoleArn=env_fixture.EnvironmentDefaultIAMRoleArn,
            SamlAdminGroupName=env_fixture.SamlGroupName,
            VolumeSizeInGB=32,
            InstanceType='ml.t3.medium',
        )
        session.add(notebook)
    yield notebook
