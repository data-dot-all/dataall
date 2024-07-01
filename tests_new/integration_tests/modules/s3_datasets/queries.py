# TODO: This file will be replaced by using the SDK directly
from backend.dataall.modules.datasets_base.services.datasets_enums import ConfidentialityClassification
def create_dataset(client, name, owner, group, organizationUri, environmentUri, tags, autoApprovalEnabled = False, confidentiality = None):
    query = {
        'operationName': 'CreateDataset',
        'variables': {
            'input': {
                'owner': owner,
                'label': name,
                'description': 'Created for integration testing',
                'tags': tags,
                'environmentUri': environmentUri,
                'SamlAdminGroupName': group,
                'organizationUri': organizationUri,
                'confidentiality': confidentiality or ConfidentialityClassification.Unclassified.value,
                'autoApprovalEnabled': autoApprovalEnabled,
            }
        },
        'query': f"""
                  mutation CreateDataset($input: NewDatasetInput!) {{
                    createDataset(input: $input) {{
                      datasetUri
                      label
                      userRoleForDataset
                    }}
                  }}
                """,
    }
    response = client.query(query=query)
    return response.data.createDataset

def import_dataset(client, name, owner, group, organizationUri, environmentUri, tags, bucketName, KmsKeyAlias, autoApprovalEnabled = False, confidentiality = None):
    query = {
        'operationName': 'ImportDataset',
        'variables': {
            'input': {
                'owner': owner,
                'label': name,
                'description': 'Created for integration testing',
                'tags': tags,
                'environmentUri': environmentUri,
                'SamlAdminGroupName': group,
                'organizationUri': organizationUri,
                'confidentiality': confidentiality or ConfidentialityClassification.Unclassified.value,
                'autoApprovalEnabled': autoApprovalEnabled,
                'bucketName': bucketName,
                'KmsKeyAlias': KmsKeyAlias,
            }
        },
        'query': f"""
                mutation ImportDataset($input: ImportDatasetInput) {{
                  importDataset(input: $input) {{
                    datasetUri
                    label
                    userRoleForDataset
                  }}
                }}
                """,
    }
    response = client.query(query=query)
    return response.data.importDataset

def delete_dataset(client, datasetUri, deleteFromAws=True):
    query = {
        'operationName': 'deleteDataset',
        'variables': {
            'datasetUri': datasetUri,
            'deleteFromAWS': deleteFromAws
        },
        'query': f"""
                mutation deleteDataset($datasetUri: String!, $deleteFromAWS: Boolean) {{
                  deleteDataset(datasetUri: $datasetUri, deleteFromAWS: $deleteFromAWS)
                }}
                """,
    }
    response = client.query(query=query)
    return response.data.deleteDataset

def update_dataset(client, datasetUri, input: dict):
    query = {
        'operationName': 'UpdateDataset',
        'variables': {
            'datasetUri': datasetUri,
            'input': input
        },
        'query': f"""
                  mutation UpdateDataset($datasetUri: String, $input: ModifyDatasetInput) {{
                    updateDataset(datasetUri: $datasetUri, input: $input) {{
                      datasetUri
                      label
                      tags
                      userRoleForDataset
                    }}
                  }}
                """,
    }
    response = client.query(query=query)
    return response.data.updateDataset
