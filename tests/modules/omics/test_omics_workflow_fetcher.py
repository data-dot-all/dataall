from typing import Callable
import pytest
from dataall.base.db import Engine
from dataall.modules.omics.tasks.omics_workflows_fetcher import fetch_omics_workflows
from dataall.modules.omics.db.omics_repository import OmicsRepository


@pytest.fixture
def second_environment(env, org_fixture, group):
    yield env(
        org=org_fixture,
        account='222222222222',
        envname='second_environment',
        owner=group.owner,
        group=group.name,
        role='new-role',
    )


def test_omics_workflow_fetcher_new_workflows_single_environment(db: Engine, module_mocker, env_fixture):
    """Checks that new workflows are added to the RDS database"""

    # Given one environment and 2 READY2RUN workflows returned from that account
    items = [
        {'arn': 'some-arn-1', 'id': 'id-1', 'name': 'name-1', 'status': 'ACTIVE', 'type': 'READY2RUN'},
        {'arn': 'some-arn-2', 'id': 'id-2', 'name': 'name-2', 'status': 'ACTIVE', 'type': 'READY2RUN'},
    ]
    module_mocker.patch(
        'dataall.modules.omics.aws.omics_client.OmicsClient.client',
        return_value=True,
    )
    mocker = module_mocker.patch(
        'dataall.modules.omics.aws.omics_client.OmicsClient.list_workflows',
        return_value=items,
    )
    # When we run the omics workflows fetcher
    success = fetch_omics_workflows(db)
    try:
        # Then, the task completes successfully
        assert success == True
        # Then, the mocker is called only once
        mocker.assert_called_once()
        with db.scoped_session() as session:
            workflows = OmicsRepository(session).paginated_omics_workflows(filter={})
            # Then, the 2 workflows are added to RDS
            assert workflows.get('count') == 2
    finally:
        with db.scoped_session() as session:
            workflows = OmicsRepository(session).paginated_omics_workflows(filter={})
            # Finally, clean_up test
            for workflow in workflows.get('nodes'):
                session.delete(workflow)


def test_omics_workflow_fetcher_new_workflows_multiple_environments(
    db: Engine, module_mocker, env_fixture, second_environment
):
    """Checks that new workflows are added to the RDS database WITHOUT duplicating the workflows of both environments"""

    # Given 2 environment and 2 READY2RUN workflows returned from each of the accounts
    items = [
        {'arn': 'some-arn-1', 'id': 'id-1', 'name': 'name-1', 'status': 'ACTIVE', 'type': 'READY2RUN'},
        {'arn': 'some-arn-2', 'id': 'id-2', 'name': 'name-2', 'status': 'ACTIVE', 'type': 'READY2RUN'},
    ]
    module_mocker.patch(
        'dataall.modules.omics.aws.omics_client.OmicsClient.client',
        return_value=True,
    )
    mocker = module_mocker.patch(
        'dataall.modules.omics.aws.omics_client.OmicsClient.list_workflows',
        return_value=items,
    )
    # When we run the omics workflows fetcher
    success = fetch_omics_workflows(db)
    # Then, the task completes successfully
    try:
        assert success == True
        # Then, the mocker is called only once
        mocker.assert_called_once()
        with db.scoped_session() as session:
            workflows = OmicsRepository(session).paginated_omics_workflows(filter={})
            # Then, the 2 workflows are added to RDS without duplicating
            assert workflows.get('count') == 2
    finally:
        with db.scoped_session() as session:
            workflows = OmicsRepository(session).paginated_omics_workflows(filter={})
            # Finally, clean_up test
            for workflow in workflows.get('nodes'):
                session.delete(workflow)
            session.delete(second_environment)


def test_omics_workflow_fetcher_existing_workflows(db: Engine, workflow1, module_mocker):
    """Checks that existing workflows are updated in the RDS database"""

    # Given 1 environment and 3 READY2RUN workflows returned. And a workflow1 that is already saved
    with db.scoped_session() as session:
        workflows = OmicsRepository(session).paginated_omics_workflows(filter={})
        # Check only the workflow1 is initially in the test
        assert workflows.get('count') == 1
    items = [
        {'arn': 'some-arn-1', 'id': 'id-1', 'name': 'name-1', 'status': 'ACTIVE', 'type': 'READY2RUN'},
        {'arn': 'some-arn-2', 'id': 'id-2', 'name': 'name-2', 'status': 'ACTIVE', 'type': 'READY2RUN'},
        {'arn': workflow1.arn, 'id': workflow1.id, 'name': workflow1.name, 'status': 'ACTIVE', 'type': 'READY2RUN'},
    ]
    module_mocker.patch(
        'dataall.modules.omics.aws.omics_client.OmicsClient.client',
        return_value=True,
    )
    mocker = module_mocker.patch(
        'dataall.modules.omics.aws.omics_client.OmicsClient.list_workflows',
        return_value=items,
    )
    # When we run the omics workflows fetcher
    success = fetch_omics_workflows(db)
    # Then, the task completes successfully
    assert success == True
    # Then, the mocker is called once (environment of workflow1)
    mocker.assert_called_once()
    with db.scoped_session() as session:
        workflows = OmicsRepository(session).paginated_omics_workflows(filter={})
        # Then, the 2 workflows are added to RDS without duplicating
        assert workflows.get('count') == 3
