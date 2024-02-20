import boto3
import pytest

from dataall.modules.omics.db.models import OmicsRun


class OmicsClient:

    @staticmethod
    def client(awsAccountId: str, region: str):
        return boto3.Session()

    @staticmethod
    def get_omics_workflow(id: str, session):
        return True

    @staticmethod
    def get_omics_run(session, runUri: str):
        return True

    @staticmethod
    def run_omics_workflow(omics_run: OmicsRun, session):
        return True

    @staticmethod
    def list_workflows(awsAccountId, region, type):
        return True


@pytest.fixture(scope='module', autouse=True)
def patch_aws(module_mocker):
    module_mocker.patch(
        "dataall.modules.omics.services.omics_service.client",
        return_value=OmicsClient(),
    )


@pytest.fixture(scope='module', autouse=True)
def env_params():
    yield {'omicsEnabled': 'True'}


@pytest.fixture(scope='module')
def omics_run(client, group, env_fixture, dataset_fixture) -> OmicsRun:
    response = client.query(
        """
            mutation createOmicsRun($input: NewOmicsRunInput) {
              createOmicsRun(input: $input) {
                label
                runUri
              }
            }
        """,
        input={
            'label': 'my omics run',
            'SamlAdminGroupName': group.name,
            'environmentUri': env_fixture.environmentUri,
            'workflowId': 'id-1234',
            'destination': dataset_fixture.datasetUri,
            'parameterTemplate': '{"something"}',
        },
        username='alice',
        groups=[group.name],
    )
    yield response.data.createOmicsRun
