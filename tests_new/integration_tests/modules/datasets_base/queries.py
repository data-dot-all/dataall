# TODO: This file will be replaced by using the SDK directly
from backend.dataall.modules.datasets_base.services.datasets_enums import ConfidentialityClassification

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
