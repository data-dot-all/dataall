# TODO: This file will be replaced by using the SDK directly
from backend.dataall.modules.datasets_base.services.datasets_enums import ConfidentialityClassification

S3_DATASET_TYPE = """
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
S3BucketName
GlueDatabaseName
GlueCrawlerName
GlueCrawlerSchedule
GlueProfilingJobName
GlueProfilingTriggerSchedule
IAMDatasetAdminRoleArn
KmsAlias
SamlAdminGroupName
businessOwnerEmail
businessOwnerDelegationEmails
importedS3Bucket
importedGlueDatabase
importedKmsKey
importedAdminRole
imported
environment { 
  environmentUri
  label
  AwsAccountId
  region
}
organization { 
  organizationUri
  label
}
owners
stewards
userRoleForDataset
userRoleInEnvironment
statistics { 
  tables
  locations
  upvotes
}
terms {
  count
  nodes {
    __typename
    ... on Term {
      nodeUri
      path
      label
    }
  }
}
topics
confidentiality
language
stack { 
  stack
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
autoApprovalEnabled
"""


def create_dataset(
    client,
    name,
    owner,
    group,
    organizationUri,
    environmentUri,
    tags,
    autoApprovalEnabled=False,
    confidentiality=None,
):
    query = {
        'operationName': 'CreateDataset',
        'variables': {
            'input': {
                'owner': owner,
                'label': name,
                'description': 'Created for integration testing',
                'tags': tags,
                'topics': ['Sites'],
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
                        {S3_DATASET_TYPE}
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.createDataset


def import_dataset(
    client,
    name,
    owner,
    group,
    organizationUri,
    environmentUri,
    tags,
    bucketName,
    KmsKeyAlias='',
    glueDatabaseName='',
    autoApprovalEnabled=False,
    confidentiality=None,
):
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
                'glueDatabaseName': glueDatabaseName,
            }
        },
        'query': f"""
                    mutation ImportDataset($input: ImportDatasetInput) {{
                      importDataset(input: $input) {{
                        {S3_DATASET_TYPE}
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.importDataset


def delete_dataset(client, datasetUri, deleteFromAws=True):
    query = {
        'operationName': 'deleteDataset',
        'variables': {'datasetUri': datasetUri, 'deleteFromAWS': deleteFromAws},
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
        'variables': {'datasetUri': datasetUri, 'input': input},
        'query': f"""
                    mutation UpdateDataset($datasetUri: String, $input: ModifyDatasetInput) {{
                      updateDataset(datasetUri: $datasetUri, input: $input) {{
                        {S3_DATASET_TYPE}
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.updateDataset


def get_dataset(client, datasetUri):
    query = {
        'operationName': 'GetDataset',
        'variables': {'datasetUri': datasetUri},
        'query': f"""
                    query GetDataset($datasetUri: String!) {{
                      getDataset(datasetUri: $datasetUri) {{
                        {S3_DATASET_TYPE}
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.getDataset
