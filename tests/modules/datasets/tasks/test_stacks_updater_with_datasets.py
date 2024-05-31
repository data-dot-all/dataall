import pytest
from dataall.core.environment.tasks.env_stacks_updater import update_stacks


@pytest.fixture(scope='module', autouse=True)
def sync_dataset(create_dataset, org_fixture, env_fixture, db):
    yield create_dataset(org_fixture, env_fixture, 'dataset')


def test_stacks_update(db, org, env, sync_dataset, mocker):
    mocker.patch(
        'dataall.core.environment.tasks.env_stacks_updater.update_stack',
        return_value=True,
    )
    envs, datasets = update_stacks(engine=db, envname='local')
    assert envs == 1
    assert datasets == 1
