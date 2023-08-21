from dataall.core.environment.tasks.env_stacks_updater import update_stacks


def test_stacks_update(db, org_fixture, env_fixture, mocker):
    mocker.patch(
        'dataall.core.environment.tasks.env_stacks_updater.update_stack',
        return_value=True,
    )
    envs, others = update_stacks(engine=db, envname='local')
    assert envs == 1
    assert others == 0
