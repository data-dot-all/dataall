import pytest


def test_omics_run(omics_run, group):
    print('adri')
    print(omics_run)
    assert omics_run.runUri
    assert omics_run.SamlAdminGroupName == group.name
    assert omics_run.label == 'my omics run'


def test_get_omics_run():
    # TODO
    assert True


def test_get_omics_run_from_aws():
    # TODO
    assert True


def test_get_omics_workflow():
    # TODO
    assert True


def test_run_omics_workflow():
    # TODO
    assert True


def test_list_user_omics_runs(client, user, group, omics_run):
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

    assert len(response.data.listOmicsRuns['nodes']) == 1

    response = client.query(
        query,
        filter={'term': 'my omics'},
        username=user.username,
        groups=[group.name],
    )

    assert len(response.data.listOmicsRuns['nodes']) == 1


def test_nopermissions_list_user_omics_runs(client, user2, group2):
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

    assert len(response.data.listOmicsRuns['nodes']) == 0


def test_list_omics_workflows():
    # TODO
    assert True


def delete_omics_run():
    # TODO
    assert True
