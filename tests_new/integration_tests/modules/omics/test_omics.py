from assertpy import assert_that

from integration_tests.errors import GqlError
from integration_tests.modules.omics.queries import (
    list_omics_runs,
    get_omics_workflow,
    list_omics_workflows,
    create_omics_run,
    delete_omics_run
)


def test_create_smstudio_user(smstudio_user1):
    assert_that(smstudio_user1.stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')


def test_create_omics_run(omics_workflow_1):
