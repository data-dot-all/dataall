from assertpy import assert_that


def delete_omics_run(client, runUri, user, group):
    query = """
    mutation deleteOmicsRun($input: OmicsDeleteInput!) {
      deleteOmicsRun(input: $input)
    }
    """
    return client.query(
        query,
        input={
            'runUris': [runUri],
            'deleteFromAWS': True,
        },
        username=user.username,
        groups=[group.name],
    )


def list_omics_runs(client, user, group, filter=None):
    query = """
            query listOmicsRuns($filter: OmicsFilter) {
              listOmicsRuns(filter: $filter) {
                count
                page
                pages
                hasNext
                hasPrevious
                nodes {
                  runUri
                  workflowUri
                  name
                  owner
                  SamlAdminGroupName
                  outputDatasetUri
                  description
                  label
                  created
                  tags
                  environment {
                    label
                    name
                    environmentUri
                    AwsAccountId
                    region
                    SamlGroupName
                  }
                  organization {
                    label
                    name
                    organizationUri
                  }
                  workflow {
                    label
                    name
                    workflowUri
                    id
                    description
                    parameterTemplate
                    type
                  }
                  status {
                    status
                    statusMessage
                  }
                }
              }
            }
            """

    return client.query(
        query,
        filter=filter,
        username=user.username,
        groups=[group.name],
    )


def test_create_omics_run(run1, group):
    """
    Tests creation of omics Run
    """
    assert run1.runUri
    assert run1.SamlAdminGroupName == group.name
    assert run1.label == 'my omics run'


def test_create_omics_run_unauthorized(client, user2, group2, env_fixture, workflow1, dataset1):
    response = client.query(
        """
            mutation createOmicsRun($input: NewOmicsRunInput!) {
              createOmicsRun(input: $input) {
                label
                runUri
                SamlAdminGroupName
              }
            }
        """,
        input={
            'label': 'my omics run',
            'SamlAdminGroupName': group2.name,
            'environmentUri': env_fixture.environmentUri,
            'workflowUri': workflow1.workflowUri,
            'destination': dataset1.datasetUri,
            'parameterTemplate': '{"something"}',
        },
        username=user2.username,
        groups=[group2.name],
    )
    assert_that(response.errors[0].message).contains(
        'UnauthorizedOperation', 'CREATE_OMICS_RUN', env_fixture.environmentUri
    )


def test_list_user_omics_runs(client, user, group, run1):
    response = list_omics_runs(client, user, group)
    assert_that(response.data.listOmicsRuns['count']).is_equal_to(1)
    assert_that(response.data.listOmicsRuns['nodes'][0]['runUri']).is_equal_to(run1.runUri)

    response = list_omics_runs(client, user, group, filter={'term': 'my omics'})
    assert_that(response.data.listOmicsRuns['count']).is_equal_to(1)
    assert_that(response.data.listOmicsRuns['nodes'][0]['runUri']).is_equal_to(run1.runUri)


def test_list_user_omics_runs_unauthorized(client, user2, group2, run1):
    response = list_omics_runs(client, user2, group2)
    assert_that(response.data.listOmicsRuns['count']).is_equal_to(0)


def test_list_omics_workflows(client, user, group, workflow1):
    query = """
        query listOmicsWorkflows($filter: OmicsFilter) {
          listOmicsWorkflows(filter: $filter) {
            count
            page
            pages
            hasNext
            hasPrevious
            nodes {
              arn
              id
              name
              label
              workflowUri
              description
              type
              parameterTemplate
            }
          }
        }
        """

    response = client.query(
        query,
        filter=None,
        username=user.username,
        groups=[group.name],
    )
    assert response.data.listOmicsWorkflows['count'] == 1
    assert response.data.listOmicsWorkflows['nodes'][0]['label'] == workflow1.label
    assert response.data.listOmicsWorkflows['nodes'][0]['workflowUri'] == workflow1.workflowUri


def test_get_omics_workflow(client, user, group, workflow1):
    query = """
        query getOmicsWorkflow($workflowUri: String!) {
          getOmicsWorkflow(workflowUri: $workflowUri) {
            workflowUri
            id
            name
            description
            parameterTemplate
            type
          }
        }
        """

    response = client.query(
        query,
        workflowUri=workflow1.workflowUri,
        username=user.username,
        groups=[group.name],
    )
    assert response.data.getOmicsWorkflow['workflowUri'] == workflow1.workflowUri
    assert response.data.getOmicsWorkflow['id'] == workflow1.id
    assert response.data.getOmicsWorkflow['type'] == workflow1.type


def test_delete_omics_run_unauthorized(client, user2, group2, run1):
    response = delete_omics_run(client, run1.runUri, user2, group2)
    assert_that(response.errors[0].message).contains('UnauthorizedOperation', 'DELETE_OMICS_RUN', run1.runUri)


def test_delete_omics_run(client, user, group, run1):
    response = delete_omics_run(client, run1.runUri, user, group)
    assert_that(response.data.deleteOmicsRun).is_true()
    response = list_omics_runs(client, user, group)
    assert_that(response.data.listOmicsRuns['count']).is_equal_to(0)
