def list_omics_runs(client, term=None):
    query = {
        'operationName': 'listOmicsRuns',
        'variables': {'filter': {'term': term}},
        'query': """
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
          outputUri
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
            """,
    }
    response = client.query(query=query)
    return response.data.getOmicsWorkflow


def get_omics_workflow(client, workflow_uri):
    query = {
        'operationName': 'getOmicsWorkflow',
        'variables': {'workflowUri': workflow_uri},
        'query': """
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
            """,
    }
    response = client.query(query=query)
    return response.data.getOmicsWorkflow


def list_omics_workflows(client, filter):
    query = {
        'operationName': 'listOmicsWorkflows',
        'variables': {'filter': filter},
        'query': """
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
            """,
    }
    response = client.query(query=query)
    return response.data.listOmicsWorkflows


def create_omics_run(client, input):
    query = {
        'operationName': 'createOmicsRun',
        'variables': {'input': input},
        'query': """
                mutation createOmicsRun($input: NewOmicsRunInput!) {
      createOmicsRun(input: $input) {
        label
        runUri
      }
    }
        """,
    }
    response = client.query(query=query)
    return response.data.createOmicsRun


def delete_omics_run(client, run_uris):
    query = {
        'operationName': 'deleteOmicsRun',
        'variables': {'input': {'runUris': run_uris, 'deleteFromAWS': True}},
        'query': """
            mutation deleteOmicsRun($input: OmicsDeleteInput!) {
              deleteOmicsRun(input: $input)
            }
            """,
    }
    response = client.query(query=query)
    return response.data.deleteOmicsRun
