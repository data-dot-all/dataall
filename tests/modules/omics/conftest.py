import boto3
import pytest
import typing

from dataall.modules.omics.db.omics_models import OmicsRun, OmicsWorkflow
from dataall.modules.datasets_base.db.dataset_models import Dataset
from dataall.core.environment.db.environment_models import Environment
from dataall.core.organizations.db.organization_models import Organization


@pytest.fixture(scope='module', autouse=True)
def patch_aws(module_mocker):
    response_dict = dict()
    response_dict['id'] = '1234'
    module_mocker.patch(
        'dataall.modules.omics.aws.omics_client.OmicsClient.run_omics_workflow',
        return_value=response_dict,
    )
    module_mocker.patch(
        'dataall.modules.omics.aws.omics_client.OmicsClient.get_omics_workflow',
        return_value=response_dict,
    )
    module_mocker.patch(
        'dataall.modules.omics.aws.omics_client.OmicsClient.get_omics_run',
        return_value=response_dict,
    )
    module_mocker.patch(
        'dataall.modules.omics.aws.omics_client.OmicsClient.list_workflows',
        return_value=response_dict,
    )


@pytest.fixture(scope='module', autouse=True)
def env_params():
    yield {'omicsEnabled': 'True'}


@pytest.fixture(scope='module')
def dataset_model(db):
    def factory(
        organization: Organization, environment: Environment, label: str, autoApprovalEnabled: bool = False
    ) -> Dataset:
        with db.scoped_session() as session:
            dataset = Dataset(
                organizationUri=organization.organizationUri,
                environmentUri=environment.environmentUri,
                label=label,
                owner=environment.owner,
                stewards=environment.SamlGroupName,
                SamlAdminGroupName=environment.SamlGroupName,
                businessOwnerDelegationEmails=['foo@amazon.com'],
                name=label,
                S3BucketName=label,
                GlueDatabaseName='gluedatabase',
                KmsAlias='kmsalias',
                AwsAccountId=environment.AwsAccountId,
                region=environment.region,
                IAMDatasetAdminUserArn=f'arn:aws:iam::{environment.AwsAccountId}:user/dataset',
                IAMDatasetAdminRoleArn=f'arn:aws:iam::{environment.AwsAccountId}:role/dataset',
                autoApprovalEnabled=autoApprovalEnabled,
            )
            session.add(dataset)
            session.commit()
            return dataset

    yield factory


@pytest.fixture(scope='module')
def dataset1(dataset_model: typing.Callable, org_fixture, env_fixture) -> Dataset:
    yield dataset_model(organization=org_fixture, environment=env_fixture, label='datasetomics')


@pytest.fixture(scope='module')
def omics_workflow_model(db):
    def factory(environment: Environment, label: str) -> OmicsWorkflow:
        with db.scoped_session() as session:
            workflow = OmicsWorkflow(
                environmentUri=environment.environmentUri,
                label=label,
                owner=environment.owner,
                name=label,
                arn='some-arn',
                id='some-id',
                type='READY2RUN',
            )
            session.add(workflow)
            session.commit()
            return workflow

    yield factory


@pytest.fixture(scope='module')
def workflow1(omics_workflow_model: typing.Callable, env_fixture) -> Dataset:
    yield omics_workflow_model(environment=env_fixture, label='workflow1')


@pytest.fixture(scope='module')
def omics_run(client, group, env_fixture, dataset1, workflow1) -> OmicsRun:
    response = client.query(
        """
            mutation createOmicsRun($input: NewOmicsRunInput) {
              createOmicsRun(input: $input) {
                label
                runUri
                SamlAdminGroupName
              }
            }
        """,
        input={
            'label': 'my omics run',
            'SamlAdminGroupName': group.name,
            'environmentUri': env_fixture.environmentUri,
            'workflowUri': workflow1.workflowUri,
            'destination': dataset1.datasetUri,
            'parameterTemplate': '{"something"}',
        },
        username='alice',
        groups=[group.name],
    )
    yield response.data.createOmicsRun
