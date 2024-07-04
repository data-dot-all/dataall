# TODO: This file will be replaced by using the SDK directly

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
                'confidentiality': confidentiality or 'Unclassified',
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


def get_dataset_assume_role_url(client, datasetUri):
    query = {
        'operationName': 'GetDatasetAssumeRoleUrl',
        'variables': {'datasetUri': datasetUri},
        'query': f"""
                    query GetDatasetAssumeRoleUrl($datasetUri: String!) {{
                      getDatasetAssumeRoleUrl(datasetUri: $datasetUri)
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.getDatasetAssumeRoleUrl


def generate_dataset_access_token(client, datasetUri):
    query = {
        'operationName': 'GenerateDatasetAccessToken',
        'variables': {'datasetUri': datasetUri},
        'query': f"""
                    mutation GenerateDatasetAccessToken($datasetUri: String!) {{
                      generateDatasetAccessToken(datasetUri: $datasetUri)
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.generateDatasetAccessToken


def get_dataset_presigned_role_url(client, datasetUri, input):
    query = {
        'operationName': 'GetDatasetPresignedUrl',
        'variables': {'datasetUri': datasetUri, 'input': input},
        'query': f"""
                    query GetDatasetPresignedUrl(
                      $datasetUri: String!
                      $input: DatasetPresignedUrlInput
                    ) {{
                      getDatasetPresignedUrl(datasetUri: $datasetUri, input: $input)
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.getDatasetPresignedUrl


def start_glue_Crawler(client, datasetUri, input):
    query = {
        'operationName': 'StartGlueCrawler',
        'variables': {'datasetUri': datasetUri, 'input': input},
        'query': f"""
                    mutation StartGlueCrawler($datasetUri: String, $input: CrawlerInput) {{
                      startGlueCrawler(datasetUri: $datasetUri, input: $input) {{
                        Name
                        AwsAccountId
                        region
                        status
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.startGlueCrawler


def sync_tables(client, datasetUri):
    query = {
        'operationName': 'SyncTables',
        'variables': {'datasetUri': datasetUri},
        'query': f"""
                    mutation SyncTables($datasetUri: String!) {{
                      syncTables(datasetUri: $datasetUri) {{
                        count
                        nodes {{
                          tableUri
                          GlueTableName
                          GlueDatabaseName
                          description
                          name
                          label
                          created
                          S3Prefix
                          dataset {{
                            datasetUri
                            name
                            GlueDatabaseName
                            userRoleForDataset
                          }}
                        }}
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.syncTables


def preview_table(client, tableUri):
    query = {
        'operationName': 'PreviewTable',
        'variables': {'tableUri': tableUri},
        'query': f"""
                    query PreviewTable($tableUri: String!) {{
                      previewTable(tableUri: $tableUri) {{
                        rows
                        fields
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.previewTable


def start_dataset_profiling_run(client, input):
    query = {
        'operationName': 'startDatasetProfilingRun',
        'variables': {'input': input},
        'query': f"""
                    mutation startDatasetProfilingRun($input: StartDatasetProfilingRunInput!) {{
                      startDatasetProfilingRun(input: $input) {{
                        profilingRunUri
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.startDatasetProfilingRun


def delete_table(client, tableUri):
    query = {
        'operationName': 'deleteDatasetTable',
        'variables': {'tableUri': tableUri},
        'query': f"""
                    mutation deleteDatasetTable($tableUri: String!) {{
                      deleteDatasetTable(tableUri: $tableUri)
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.deleteDatasetTable


def add_folder(client, datasetUri, input):
    query = {
        'operationName': 'CreateDatasetStorageLocation',
        'variables': {'datasetUri': datasetUri, 'input': input},
        'query': f"""
                    mutation CreateDatasetStorageLocation($datasetUri: String!, $input: NewDatasetStorageLocationInput) {{
                      createDatasetStorageLocation(datasetUri: $datasetUri, input: $input) {{
                        locationUri
                        S3Prefix
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.createDatasetStorageLocation


def delete_folder(client, locationUri):
    query = {
        'operationName': 'DeleteDatasetStorageLocation',
        'variables': {'locationUri': locationUri},
        'query': f"""
                    mutation DeleteDatasetStorageLocation($locationUri: String!) {{
                      deleteDatasetStorageLocation(locationUri: $locationUri)
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.deleteDatasetStorageLocation
