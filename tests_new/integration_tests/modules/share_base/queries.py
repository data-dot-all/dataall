from tests_new.integration_tests.modules.share_base.input_types import NewShareObjectInput
from tests_new.integration_tests.modules.share_base.types import ShareObject
from typing import List


def create_share_object(
    client,
    dataset_or_item_params: dict,
    environmentUri,
    groupUri,
    principalId,
    principalType,
    requestPurpose,
    attachMissingPolicies,
    permissions,
):
    variables = dataset_or_item_params
    variables['input'] = NewShareObjectInput(
        environmentUri, groupUri, principalId, principalType, requestPurpose, attachMissingPolicies, permissions
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


def update_share_request_reason(client, shareUri: str, reason: str):
    variables = {'shareUri': shareUri, 'requestPurpose': reason}
    query = {
        'operationName': 'updateShareRequestReason',
        'variables': variables,
        'query': f"""
                    mutation updateShareRequestReason($shareUri: String!, $requestPurpose: String!) {{
                      updateShareRequestReason(shareUri: $shareUri, requestPurpose: $requestPurpose) 
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.updateShareRequestReason


def update_share_reject_reason(client, shareUri: str, reason: str):
    variables = {'shareUri': shareUri, 'rejectPurpose': reason}
    query = {
        'operationName': 'updateShareRejectReason',
        'variables': variables,
        'query': f"""
                    mutation updateShareRejectReason($shareUri: String!, $rejectPurpose: String!) {{
                      updateShareRejectReason(shareUri: $shareUri, rejectPurpose: $rejectPurpose) 
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.updateShareRejectReason


def reject_share_object(client, shareUri: str):
    variables = {'shareUri': shareUri}
    query = {
        'operationName': 'rejectShareObject',
        'variables': variables,
        'query': f"""
                    mutation rejectShareObject($shareUri: String!) {{
                      rejectShareObject(shareUri: $shareUri) {{
                         shareUri,
                         status,
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.rejectShareObject


def approve_share_object(client, shareUri: str):
    variables = {'shareUri': shareUri}
    query = {
        'operationName': 'approveShareObject',
        'variables': variables,
        'query': f"""
                    mutation approveShareObject($shareUri: String!) {{
                      approveShareObject(shareUri: $shareUri) {{
                         shareUri,
                         status,
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.approveShareObject


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


def get_share_object(client, shareUri: str, filter=None):
    variables = {'shareUri': shareUri, 'filter': filter or {}}
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


def verify_share_items(client, shareUri: str, shareItemsUris: List[str]):
    query = {
        'operationName': 'verifyItemsShareObject',
        'variables': {'input': {'shareUri': shareUri, 'itemUris': shareItemsUris}},
        'query': f"""
                    mutation verifyItemsShareObject($input: ShareItemSelectorInput) {{
                        verifyItemsShareObject(input: $input) {{
                            shareUri
                            status
                        }}
                    }}
                """,
    }

    response = client.query(query=query)
    return response.data.verifyItemsShareObject


def revoke_share_items(client, shareUri: str, shareItemUris: List[str]):
    query = {
        'operationName': 'revokeItemsShareObject',
        'variables': {'input': {'shareUri': shareUri, 'itemUris': shareItemUris}},
        'query': f"""
                    mutation revokeItemsShareObject($input: ShareItemSelectorInput) {{
                        revokeItemsShareObject(input: $input) {{
                            shareUri
                            status
                        }}
                    }}
                """,
    }

    response = client.query(query=query)
    return response.data.revokeItemsShareObject


def remove_shared_item(client, shareItemUri):
    query = {
        'operationName': 'RemoveSharedItem',
        'variables': {'shareItemUri': shareItemUri},
        'query': """
              mutation RemoveSharedItem($shareItemUri: String!) {
                removeSharedItem(shareItemUri: $shareItemUri)
              }
                """,
    }

    response = client.query(query=query)
    return response.data.removeSharedItem


def get_s3_consumption_data(client, shareUri: str):
    query = {
        'operationName': 'getS3ConsumptionData',
        'variables': {'shareUri': shareUri},
        'query': f"""
                    query getS3ConsumptionData($shareUri: String!) {{
                        getS3ConsumptionData(shareUri: $shareUri) {{
                           s3AccessPointName
                           sharedGlueDatabase
                           s3bucketName
                        }}
                    }}
                """,
    }

    response = client.query(query=query)
    return response.data.getS3ConsumptionData
