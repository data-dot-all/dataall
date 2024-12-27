# TODO: This file will be replaced by using the SDK directly

DATASET_BASE_TYPE = """
datasetUri
label
name
description
tags
owner
created
updated
admins
AwsAccountId
region
environment { 
  environmentUri
  label
  region
}
owners
stewards
userRoleForDataset
userRoleInEnvironment
topics
confidentiality
language
autoApprovalEnabled
stack { 
  stack
  status
  stackUri
}
"""


def list_datasets(client, term=''):
    query = {
        'operationName': 'ListDatasets',
        'variables': {'filter': {'term': term}},
        'query': f"""
                  query ListDatasets($filter: DatasetFilter) {{
                    listDatasets(filter: $filter) {{
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        nodes {{
                          {DATASET_BASE_TYPE}
                       }}
                    }}
                  }}
                """,
    }
    response = client.query(query=query)
    return response.data.listDatasets


def list_owned_datasets(client, term=''):
    query = {
        'operationName': 'listOwnedDatasets',
        'variables': {'filter': {'term': term}},
        'query': f"""
                query listOwnedDatasets($filter: DatasetFilter) {{
                      listOwnedDatasets(filter: $filter) {{
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        nodes {{
                          {DATASET_BASE_TYPE}
                        }}
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.listOwnedDatasets


def list_datasets_created_in_environment(client, environment_uri, term=''):
    query = {
        'operationName': 'ListDatasetsCreatedInEnvironment',
        'variables': {'environmentUri': environment_uri, 'filter': {'term': term}},
        'query': f"""
                query ListDatasetsCreatedInEnvironment(
                      $filter: DatasetFilter
                      $environmentUri: String!
                    ) {{
                      listDatasetsCreatedInEnvironment(
                        environmentUri: $environmentUri
                        filter: $filter
                      ) {{
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        nodes {{
                          {DATASET_BASE_TYPE}
                       }}
                    }}
                  }}
                """,
    }
    response = client.query(query=query)
    return response.data.listDatasetsCreatedInEnvironment
