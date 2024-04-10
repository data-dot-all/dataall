import pytest


def test_create_omics_run(run1, group):
    """
    Tests creation of omics Run
    """
    assert run1.runUri
    assert run1.SamlAdminGroupName == group.name
    assert run1.label == 'my omics run'

def test_list_user_omics_runs(client, user, group, run1):
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

    response = client.query(
        query,
        filter=None,
        username=user.username,
        groups=[group.name],
    )

    assert response.data.listOmicsRuns['count'] == 1
    assert len(response.data.listOmicsRuns['nodes']) == 1

    response = client.query(
        query,
        filter={'term': 'my omics'},
        username=user.username,
        groups=[group.name],
    )
    assert response.data.listOmicsRuns['count'] == 1
    assert len(response.data.listOmicsRuns['nodes']) == 1


def test_nopermissions_list_user_omics_runs(client, user2, group2, run1):
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

    response = client.query(
        query,
        filter=None,
        username=user2.username,
        groups=[group2.name],
    )
    assert response.data.listOmicsRuns['count'] == 0
    assert len(response.data.listOmicsRuns['nodes']) == 0


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
