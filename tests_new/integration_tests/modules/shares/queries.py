from tests_new.integration_tests.modules.shares.input_types import NewShareObjectInput
from tests_new.integration_tests.modules.shares.types import ShareObject


def create_share_object(client, dataset_or_item_params: dict, environmentUri, groupUri, principalId, principalType,
                        requestPurpose, attachMissingPolicies):
    variables = dataset_or_item_params
    variables['input'] = NewShareObjectInput(environmentUri, groupUri, principalId, principalType, requestPurpose,
                                             attachMissingPolicies)
    query = {
        'operationName': 'createShareObject',
        'variables': variables,
        'query': f"""
                    mutation createShareObject(        $datasetUri: String!
        $itemType: String
        $itemUri: String
        $input: NewShareObjectInput!) {{
                      createShareObject(
          datasetUri: $datasetUri
          itemType: $itemType
          itemUri: $itemUri
          input: $input
        ) {{
                        {ShareObject}
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.createShareObject
