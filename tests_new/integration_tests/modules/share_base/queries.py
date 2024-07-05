from tests_new.integration_tests.modules.share_base.input_types import NewShareObjectInput
from tests_new.integration_tests.modules.share_base.types import ShareObject


def create_share_object(
    client,
    dataset_or_item_params: dict,
    environmentUri,
    groupUri,
    principalId,
    principalType,
    requestPurpose,
    attachMissingPolicies,
):
    variables = dataset_or_item_params
    variables['input'] = NewShareObjectInput(
        environmentUri, groupUri, principalId, principalType, requestPurpose, attachMissingPolicies
    )
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
                        shareUri,
                        status,
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.createShareObject


def submit_share_object(client, shareUri: str):
    variables = {'shareUri': shareUri}
    query = {
        'operationName': 'submitShareObject',
        'variables': variables,
        'query': f"""
                    mutation submitShareObject($shareUri: String!) {{
                      submitShareObject(shareUri: $shareUri) {{
                         shareUri,
                         status,
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.submitShareObject


def delete_share_object(client, shareUri: str):
    variables = {'shareUri': shareUri}
    query = {
        'operationName': 'deleteShareObject',
        'variables': variables,
        'query': f"""
                    mutation deleteShareObject($shareUri: String!) {{
                    deleteShareObject(shareUri: $shareUri)
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.deleteShareObject


def get_share_object(client, shareUri: str):
    variables = {'shareUri': shareUri, 'filter': {}}
    query = {
        'operationName': 'getShareObject',
        'variables': variables,
        'query': f"""
                    query getShareObject($shareUri: String!, $filter: ShareableObjectFilter) {{
                      getShareObject(shareUri: $shareUri) {{
                        {ShareObject}
                      }}
                    }}
                """,
    }

    response = client.query(query=query)
    return response.data.getShareObject


def add_share_item(client, shareUri: str, itemUri: str, itemType: str):
    query = {
        'operationName': 'addSharedItem',
        'variables': {'shareUri': shareUri, 'input': {'itemUri': itemUri, 'itemType': itemType}},
        'query': f"""
                    mutation addSharedItem($shareUri: String!, $input: AddSharedItemInput!) {{
                        addSharedItem(shareUri: $shareUri, input: $input) {{
                             shareItemUri
                        }}
                    }}
                """,
    }

    response = client.query(query=query)
    return response.data.addSharedItem.shareItemUri
