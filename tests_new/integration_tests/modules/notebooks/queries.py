NOTEBOOK_TYPE = """
notebookUri
name
owner
description
label
created
tags
NotebookInstanceStatus
SamlAdminGroupName
RoleArn
VpcId
SubnetId
VolumeSizeInGB
InstanceType
environment {
  label
  name
  environmentUri
  AwsAccountId
  region
}
organization {
  label
  name
  organizationUri
}
stack {
  stack
  name
  status
  stackUri
  targetUri
  accountid
  region
  stackid
  link
  outputs
  resources
}
"""


def create_sagemaker_notebook(
    client,
    name,
    group,
    environmentUri,
    tags,
    VpcId,
    SubnetId,
    VolumeSizeInGB=32,
    InstanceType='ml.t3.medium',
):
    query = {
        'operationName': 'CreateSagemakerNotebook',
        'variables': {
            'input': {
                'label': name,
                'SamlAdminGroupName': group,
                'environmentUri': environmentUri,
                'VpcId': VpcId,
                'SubnetId': SubnetId,
                'description': 'Created for integration testing',
                'tags': tags,
                'VolumeSizeInGB': VolumeSizeInGB,
                'InstanceType': InstanceType,
            }
        },
        'query': f"""
                    mutation CreateSagemakerNotebook($input: NewSagemakerNotebookInput) {{
                      createSagemakerNotebook(input: $input) {{
                        {NOTEBOOK_TYPE}
                      }}
                    }}
                """,
    }

    response = client.query(query=query)
    return response.data.createSagemakerNotebook


def get_sagemaker_notebook(client, notebookUri):
    query = {
        'operationName': 'getSagemakerNotebook',
        'variables': {'notebookUri': notebookUri},
        'query': f"""
                    query getSagemakerNotebook($notebookUri: String!) {{
                      getSagemakerNotebook(notebookUri: $notebookUri) {{
                        {NOTEBOOK_TYPE}  
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.getSagemakerNotebook


def delete_sagemaker_notebook(client, notebookUri, deleteFromAWS=True):
    query = {
        'operationName': 'deleteSagemakerNotebook',
        'variables': {
            'notebookUri': notebookUri,
            'deleteFromAWS': deleteFromAWS,
        },
        'query': """
                    mutation deleteSagemakerNotebook(
                      $notebookUri: String!
                      $deleteFromAWS: Boolean
                    ) {
                      deleteSagemakerNotebook(
                        notebookUri: $notebookUri
                        deleteFromAWS: $deleteFromAWS
                      )
                    }
                """,
    }
    response = client.query(query=query)
    return response


def list_sagemaker_notebooks(client, term=''):
    query = {
        'operationName': 'ListSagemakerNotebooks',
        'variables': {
            'filter': {'term': term},
        },
        'query': f"""
                    query ListSagemakerNotebooks($filter: SagemakerNotebookFilter) {{
                      listSagemakerNotebooks(filter: $filter) {{
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        nodes {{
                            {NOTEBOOK_TYPE}
                        }}
                      }}
                    }}
                """,
    }

    response = client.query(query=query)
    return response.data.listSagemakerNotebooks


def stop_sagemaker_notebook(client, notebookUri):
    query = {
        'operationName': 'StopSagemakerNotebook',
        'variables': {
            'notebookUri': notebookUri,
        },
        'query': f"""
                    mutation StopSagemakerNotebook($notebookUri: String!) {{
                      stopSagemakerNotebook(notebookUri: $notebookUri)
                    }}
                """,
    }

    response = client.query(query=query)
    return response.data.stopSagemakerNotebook


def start_sagemaker_notebook(client, notebookUri):
    query = {
        'operationName': 'StartSagemakerNotebook',
        'variables': {
            'notebookUri': notebookUri,
        },
        'query': f"""
                    mutation StartSagemakerNotebook($notebookUri: String!) {{
                      startSagemakerNotebook(notebookUri: $notebookUri)
                    }}
                """,
    }

    response = client.query(query=query)
    return response.data.startSagemakerNotebook
