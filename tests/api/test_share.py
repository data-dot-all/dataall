import random
import typing
import pytest

import dataall


def random_table_name():
    def cpltz(l):
        return [item.capitalize() for item in l]

    prefixes = cpltz(['big', 'small', 'shiny', 'fat', 'light', 'fun', 'clean'])
    topics = cpltz(['sales', 'resources', 'receipts', 'orders', 'shipping'])
    formats = cpltz(['csv', 'parquet', 'avro', 'orc', 'txt', 'delta'])

    return f'{random.choice(prefixes)}{random.choice(topics)}{random.choice(formats)}'


@pytest.fixture(scope='module')
def org1(org: typing.Callable, user, group, tenant):
    # user, group and tenant are fixtures defined in conftest
    yield org('testorg', user.userName, group.name)


@pytest.fixture(scope='module')
def env1(environment: typing.Callable, org1: dataall.db.models.Organization, user, group
         ) -> dataall.db.models.Environment:
    # user, group and tenant are fixtures defined in conftest
    yield environment(
        organization=org1,
        awsAccountId="1" * 12,
        label="source_environment",
        owner=user.userName,
        samlGroupName=group.name,
        environmentDefaultIAMRoleName=f"source-{group.name}",
        dashboardsEnabled=False,
    )


@pytest.fixture(scope='module')
def env1group(environment_group: typing.Callable, env1, user, group
              ) -> dataall.db.models.EnvironmentGroup:
    yield environment_group(
        environment=env1,
        group=group,
    )


@pytest.fixture(scope='module')
def dataset1(dataset_model: typing.Callable, org1: dataall.db.models.Organization, env1: dataall.db.models.Environment
             ) -> dataall.db.models.Dataset:
    yield dataset_model(
        organization=org1,
        environment=env1,
        label="datasettoshare"
    )


@pytest.fixture(scope='module')
def tables1(table: typing.Callable, dataset1: dataall.db.models.Dataset):
    for i in range(1, 100):
        table(dataset1, name=random_table_name(), username=dataset1.owner)


@pytest.fixture(scope="module", autouse=True)
def table1(table: typing.Callable, dataset1: dataall.db.models.Dataset,
           user: dataall.db.models.User) -> dataall.db.models.DatasetTable:
    yield table(
        dataset=dataset1,
        name="table1",
        username=user.userName
    )


@pytest.fixture(scope='module')
def org2(org: typing.Callable, user2, group2, tenant) -> dataall.db.models.Organization:
    yield org('org2', user2.userName, group2.name)


@pytest.fixture(scope='module')
def env2(
        environment: typing.Callable, org2: dataall.db.models.Organization, user2, group2
) -> dataall.db.models.Environment:
    # user, group and tenant are fixtures defined in conftest
    yield environment(
        organization=org2,
        awsAccountId="2" * 12,
        label="target_environment",
        owner=user2.userName,
        samlGroupName=group2.name,
        environmentDefaultIAMRoleName=f"source-{group2.name}",
        dashboardsEnabled=False,
    )


@pytest.fixture(scope='module')
def dataset2(
        dataset_model: typing.Callable, org2: dataall.db.models.Organization, env2: dataall.db.models.Environment
) -> dataall.db.models.Dataset:
    yield dataset_model(
        organization=org2,
        environment=env2,
        label="datasettoshare2"
    )


@pytest.fixture(scope='module')
def tables2(table, dataset2):
    for i in range(1, 100):
        table(dataset2, name=random_table_name(), username=dataset2.owner)


@pytest.fixture(scope="module", autouse=True)
def table2(table: typing.Callable, dataset2: dataall.db.models.Dataset,
           user2: dataall.db.models.User) -> dataall.db.models.DatasetTable:
    yield table(
        dataset=dataset2,
        name="table2",
        username=user2.userName
    )


@pytest.fixture(scope='module')
def env2group(environment_group: typing.Callable, env2, user2, group2) -> dataall.db.models.EnvironmentGroup:
    yield environment_group(
        environment=env2,
        group=group2,
    )


@pytest.fixture(scope='function')
def share1_draft(
        db,
        client,
        user2,
        group2,
        share: typing.Callable,
        dataset1: dataall.db.models.Dataset,
        env2: dataall.db.models.Environment,
        env2group: dataall.db.models.EnvironmentGroup,
) -> dataall.db.models.ShareObject:
    share1 = share(
        dataset=dataset1,
        environment=env2,
        env_group=env2group,
        owner=user2.userName,
        status=dataall.api.constants.ShareObjectStatus.Draft.value
    )
    yield share1

    # Cleanup share
    # First try to direct delete. This fixture should not have any shared items, but just in case
    delete_share_object_response = delete_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share1.shareUri
    )

    if delete_share_object_response.data.deleteShareObject == True:
        return

    # Given share item in shared states
    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share1.shareUri,
        filter={"isShared": True},
    )
    revoked_items_uris = [node.shareItemUri for node in
                          get_share_object_response.data.getShareObject.get('items').nodes]

    # Then delete via revoke items if still items present
    revoke_items_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share1.shareUri,
        revoked_items_uris=revoked_items_uris

    )

    _successfull_processing_for_share_object(db, share1)

    delete_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share1.shareUri
    )


@pytest.fixture(scope='function')
def share1_item_pa(
        share_item: typing.Callable,
        share1_draft: dataall.db.models.ShareObject,
        table1: dataall.db.models.DatasetTable
) -> dataall.db.models.ShareObjectItem:
    # Cleaned up with share1_draft
    yield share_item(
        share=share1_draft,
        table=table1,
        status=dataall.api.constants.ShareItemStatus.PendingApproval.value
    )


@pytest.fixture(scope='function')
def share2_submitted(
        db,
        client,
        user2,
        group2,
        share: typing.Callable,
        dataset1: dataall.db.models.Dataset,
        env2: dataall.db.models.Environment,
        env2group: dataall.db.models.EnvironmentGroup,
) -> dataall.db.models.ShareObject:
    share2 = share(
        dataset=dataset1,
        environment=env2,
        env_group=env2group,
        owner=user2.userName,
        status=dataall.api.constants.ShareObjectStatus.Submitted.value
    )
    yield share2
    # Cleanup share
    # First try to direct delete
    delete_share_object_response = delete_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share2.shareUri
    )

    if delete_share_object_response.data.deleteShareObject == True:
        return

    # Given share item in shared states
    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share2.shareUri,
        filter={"isShared": True},
    )
    revoked_items_uris = [node.shareItemUri for node in
                          get_share_object_response.data.getShareObject.get('items').nodes]

    # Then delete via revoke items if still items present
    revoke_items_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share2.shareUri,
        revoked_items_uris=revoked_items_uris

    )
    _successfull_processing_for_share_object(db, share2)

    delete_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share2.shareUri
    )


@pytest.fixture(scope='function')
def share2_item_pa(
        share_item: typing.Callable,
        share2_submitted: dataall.db.models.ShareObject,
        table1: dataall.db.models.DatasetTable
) -> dataall.db.models.ShareObjectItem:
    # Cleaned up with share2
    yield share_item(
        share=share2_submitted,
        table=table1,
        status=dataall.api.constants.ShareItemStatus.PendingApproval.value
    )


@pytest.fixture(scope='function')
def share3_processed(
        db,
        client,
        user2,
        group2,
        share: typing.Callable,
        dataset1: dataall.db.models.Dataset,
        env2: dataall.db.models.Environment,
        env2group: dataall.db.models.EnvironmentGroup,
) -> dataall.db.models.ShareObject:
    share3 = share(
        dataset=dataset1,
        environment=env2,
        env_group=env2group,
        owner=user2.userName,
        status=dataall.api.constants.ShareObjectStatus.Processed.value
    )
    yield share3
    # Cleanup share
    # First try to direct delete
    delete_share_object_response = delete_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share3.shareUri
    )

    if delete_share_object_response.data.deleteShareObject == True:
        return

    # Given share item in shared states
    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share3.shareUri,
        filter={"isShared": True},
    )
    revoked_items_uris = [node.shareItemUri for node in
                          get_share_object_response.data.getShareObject.get('items').nodes]

    # Then delete via revoke items if still items present
    revoke_items_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share3.shareUri,
        revoked_items_uris=revoked_items_uris

    )
    _successfull_processing_for_share_object(db, share3)

    delete_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share3.shareUri
    )


@pytest.fixture(scope='function')
def share3_item_shared(
        share_item: typing.Callable,
        share3_processed: dataall.db.models.ShareObject,
        table1: dataall.db.models.DatasetTable
) -> dataall.db.models.ShareObjectItem:
    # Cleaned up with share3
    yield share_item(
        share=share3_processed,
        table=table1,
        status=dataall.api.constants.ShareItemStatus.Share_Succeeded.value
    )


@pytest.fixture(scope='function')
def share4_draft(
        user2,
        share: typing.Callable,
        dataset1: dataall.db.models.Dataset,
        env2: dataall.db.models.Environment,
        env2group: dataall.db.models.EnvironmentGroup,
) -> dataall.db.models.ShareObject:
    yield share(
        dataset=dataset1,
        environment=env2,
        env_group=env2group,
        owner=user2.userName,
        status=dataall.api.constants.ShareObjectStatus.Draft.value
    )


def test_init(tables1, tables2):
    assert True


# Queries & mutations
def create_share_object(client, userName, group, groupUri, environmentUri, datasetUri, itemUri=None):
    q = """
      mutation CreateShareObject(
        $datasetUri: String!
        $itemType: String
        $itemUri: String
        $input: NewShareObjectInput
      ) {
        createShareObject(
          datasetUri: $datasetUri
          itemType: $itemType
          itemUri: $itemUri
          input: $input
        ) {
          shareUri
          created
          status
          userRoleForShareObject
        }
      }
    """

    response = client.query(
        q,
        username=userName,
        groups=[group.name],
        datasetUri=datasetUri,
        itemType=dataall.api.constants.ShareableType.Table.value if itemUri else None,
        itemUri=itemUri,
        input={
            'environmentUri': environmentUri,
            'groupUri': groupUri,
            'principalId': groupUri,
            'principalType': dataall.api.constants.PrincipalType.Group.value,
        },
    )

    # Print response
    print('Create share request response: ', response)
    return response


def get_share_object(client, user, group, shareUri, filter):
    q = """
    query getShareObject($shareUri: String!, $filter: ShareableObjectFilter) {
      getShareObject(shareUri: $shareUri) {
        shareUri
        created
        owner
        status
        userRoleForShareObject
        principal {
          principalId
          principalType
          principalName
          principalIAMRoleName
          SamlGroupName
          environmentUri
          environmentName
          AwsAccountId
          region
          organizationUri
          organizationName
        }
        items(filter: $filter) {
          count
          page
          pages
          hasNext
          hasPrevious
          nodes {
            itemUri
            shareItemUri
            itemType
            itemName
            status
            action
          }
        }
        dataset {
          datasetUri
          datasetName
          SamlAdminGroupName
          environmentName
          exists
        }
      }
    }
    """

    response = client.query(
        q,
        username=user.userName,
        groups=[group.name],
        shareUri=shareUri,
        filter=filter,
    )
    # Print response
    print('Get share request response: ', response)
    return response


def list_dataset_share_objects(client, user, group, datasetUri):
    q = """
        query ListDatasetShareObjects(
              $datasetUri: String!
              $filter: ShareObjectFilter
            ) {
              getDataset(datasetUri: $datasetUri) {
                shares(filter: $filter) {
                  page
                  pages
                  pageSize
                  hasPrevious
                  hasNext
                  count
                  nodes {
                    owner
                    created
                    deleted
                    shareUri
                    status
                    userRoleForShareObject
                    principal {
                      principalId
                      principalType
                      principalName
                      AwsAccountId
                      region
                    }
                    statistics {
                      tables
                      locations
                    }
                    dataset {
                      datasetUri
                      datasetName
                      SamlAdminGroupName
                      environmentName
                    }
                  }
                }
              }
            }
    """

    response = client.query(
        q,
        username=user.userName,
        groups=[group.name],
        datasetUri=datasetUri,
    )
    # Print response
    print('List Dataset share objects response: ', response)
    return response


def get_share_requests_to_me(client, user, group):
    q = """
        query getShareRequestsToMe($filter: ShareObjectFilter){
            getShareRequestsToMe(filter: $filter){
                count
                nodes{
                    shareUri
                }
            }
        }
    """
    response = client.query(
        q,
        username=user.userName,
        groups=[group.name]
    )
    # Print response
    print('Get share requests to me response: ', response)
    return response


def get_share_requests_from_me(client, user, group):
    q = """
        query getShareRequestsFromMe($filter: ShareObjectFilter){
            getShareRequestsFromMe(filter: $filter){
                count
                nodes{
                    shareUri
                 }
            }
        }
    """
    response = client.query(
        q,
        username=user.userName,
        groups=[group.name]
    )
    # Print response
    print('Get share requests from me response: ', response)
    return response


def add_share_item(client, user, group, shareUri, itemUri, itemType):
    q = """
        mutation AddSharedItem($shareUri:String!,$input:AddSharedItemInput){
            addSharedItem(shareUri:$shareUri,input:$input){
                shareUri
                shareItemUri
                itemUri
                status
                action
            }
        }
        """

    response = client.query(
        q,
        username=user.userName,
        groups=[group.name],
        shareUri=shareUri,
        input={
            'itemUri': itemUri,
            'itemType': itemType,
        },
    )

    print('Response from addSharedItem: ', response)
    return response


def remove_share_item(client, user, group, shareItemUri):
    q = """
    mutation RemoveSharedItem($shareItemUri: String!) {
      removeSharedItem(shareItemUri: $shareItemUri)
    }
    """

    response = client.query(
        q,
        username=user.userName,
        groups=[group.name],
        shareItemUri=shareItemUri
    )

    print('Response from removeSharedItem: ', response)
    return response


def submit_share_object(client, user, group, shareUri):
    q = """
        mutation submitShareObject($shareUri:String!){
            submitShareObject(shareUri:$shareUri){
                status
                owner
                userRoleForShareObject
                items {
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    nodes {
                        itemUri
                        shareItemUri
                        itemType
                        itemName
                        status
                        action
                    }
                }
            }
        }
        """

    response = client.query(
        q,
        username=user.userName,
        groups=[group.name],
        shareUri=shareUri,
    )

    print('Response from submitShareObject: ', response)
    return response


def approve_share_object(client, user, group, shareUri):
    q = """
            mutation approveShareObject($shareUri:String!){
                approveShareObject(shareUri:$shareUri){
                    status
                    owner
                    userRoleForShareObject
                }
            }
            """

    response = client.query(
        q,
        username=user.userName,
        groups=[group.name],
        shareUri=shareUri,
    )

    print('Response from approveShareObject: ', response)
    return response


def reject_share_object(client, user, group, shareUri):
    q = """
    mutation RejectShareObject($shareUri: String!) {
      rejectShareObject(shareUri: $shareUri) {
        shareUri
        status
      }
    }
    """

    response = client.query(
        q,
        username=user.userName,
        groups=[group.name],
        shareUri=shareUri,
    )

    print('Response from rejectShareObject: ', response)
    return response


def revoke_items_share_object(client, user, group, shareUri, revoked_items_uris):
    q = """
        mutation revokeItemsShareObject($input: RevokeItemsInput) {
            revokeItemsShareObject(input: $input) {
                shareUri
                status
            }
        }
        """

    response = client.query(
        q,
        username=user.userName,
        groups=[group.name],
        input={
            'shareUri': shareUri,
            'revokedItemUris': revoked_items_uris
        },
    )
    print('Response from revokeItemsShareObject: ', response)
    return response


def delete_share_object(client, user, group, shareUri):
    q = """
        mutation DeleteShareObject($shareUri: String!){
          deleteShareObject(shareUri:$shareUri)
        }
    """
    response = client.query(
        q,
        username=user,
        groups=[group.name],
        shareUri=shareUri,
    )
    print('Response from deleteShareObject: ', response)
    return response


def list_datasets_published_in_environment(client, user, group, environmentUri):
    q = """
        query searchEnvironmentDataItems(
            $environmentUri:String!, $filter:EnvironmentDataItemFilter
        ){
            searchEnvironmentDataItems(environmentUri:$environmentUri, filter:$filter){
                count
                nodes{
                    shareUri
                    environmentName
                    environmentUri
                    organizationName
                    organizationUri
                    datasetUri
                    datasetName
                    itemType
                    itemAccess
                    GlueDatabaseName
                    GlueTableName
                    S3AccessPointName
                    created
                    principalId
                }
            }
        }
    """
    response = client.query(
        q,
        username=user.userName,
        groups=[group.name],
        environmentUri=environmentUri,
        filter={},
    )
    print("searchEnvironmentDataItems response: ", response)
    return response


# Tests
def test_create_share_object_unauthorized(client, group3, dataset1, env2, env2group):
    # Given
    # Existing dataset, target environment and group
    # When a user that does not belong to environment and group creates request
    create_share_object_response = create_share_object(
        client=client,
        userName='anonymous',
        group=group3,
        groupUri=env2group.groupUri,
        environmentUri=env2.environmentUri,
        datasetUri=dataset1.datasetUri
    )
    # Then, user gets Unauthorized error
    assert 'Unauthorized' in create_share_object_response.errors[0].message


def test_create_share_object_authorized(client, user2, group2, env2group, env2, dataset1):
    # Given
    # Existing dataset, target environment and group
    # When a user that belongs to environment and group creates request
    create_share_object_response = create_share_object(
        client=client,
        userName=user2.userName,
        group=group2,
        groupUri=env2group.groupUri,
        environmentUri=env2.environmentUri,
        datasetUri=dataset1.datasetUri
    )
    # Then share object created with status Draft and user is 'Requester'
    assert create_share_object_response.data.createShareObject.shareUri
    assert create_share_object_response.data.createShareObject.status == dataall.api.constants.ShareObjectStatus.Draft.value
    assert create_share_object_response.data.createShareObject.userRoleForShareObject == 'Requesters'


def test_create_share_object_with_item_authorized(client, user2, group2, env2group, env2, dataset1, table1):
    # Given
    # Existing dataset, table, target environment and group
    # When a user that belongs to environment and group creates request with table in the request
    create_share_object_response = create_share_object(
        client=client,
        userName=user2.userName,
        group=group2,
        groupUri=env2group.groupUri,
        environmentUri=env2.environmentUri,
        datasetUri=dataset1.datasetUri,
        itemUri=table1.tableUri
    )

    # Then share object created with status Draft and user is 'Requester'
    assert create_share_object_response.data.createShareObject.shareUri
    assert create_share_object_response.data.createShareObject.status == dataall.api.constants.ShareObjectStatus.Draft.value
    assert create_share_object_response.data.createShareObject.userRoleForShareObject == 'Requesters'

    # And item has been added to the share request
    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=create_share_object_response.data.createShareObject.shareUri,
        filter={"isShared": True}
    )

    assert get_share_object_response.data.getShareObject.get('items').nodes[0].itemUri == table1.tableUri
    assert get_share_object_response.data.getShareObject.get('items').nodes[
               0].itemType == dataall.api.constants.ShareableType.Table.name


def test_get_share_object(client, share1_draft, user, group):
    # Given
    # Existing share object in status Draft (->fixture share1_draft)
    # When a user from the approvers group gets the share object
    get_share_object_response = get_share_object(
        client=client,
        user=user,
        group=group,
        shareUri=share1_draft.shareUri,
        filter={}
    )
    # Then we get the info about the share
    assert get_share_object_response.data.getShareObject.shareUri == share1_draft.shareUri
    assert get_share_object_response.data.getShareObject.get(
        'principal').principalType == dataall.api.constants.PrincipalType.Group.name
    assert get_share_object_response.data.getShareObject.get('principal').principalIAMRoleName
    assert get_share_object_response.data.getShareObject.get('principal').SamlGroupName
    assert get_share_object_response.data.getShareObject.get('principal').region


def test_list_dataset_share_objects_approvers(
        client, user, group, share1_draft, dataset1
):
    # Given
    # Existing share object in status Draft (->fixture share1_draft) + share object (-> fixture share)
    # When a user from the Approvers group lists the share objects for a dataset
    list_dataset_share_objects_response = list_dataset_share_objects(
        client=client,
        user=user,
        group=group,
        datasetUri=dataset1.datasetUri
    )
    # Then, userRoleForShareObject is Approvers
    assert list_dataset_share_objects_response.data.getDataset.shares.count == 2
    assert list_dataset_share_objects_response.data.getDataset.shares.nodes[0].userRoleForShareObject == 'Approvers'


def test_list_dataset_share_objects_unauthorized(
        client, user3, group4, share1_draft, dataset1
):
    # Given
    # Existing share object in status Draft (->fixture share1_draft) + share object (-> fixture share)
    # When a user from neither Approvers or Requesters group lists the share objects for a dataset
    list_dataset_share_objects_response = list_dataset_share_objects(
        client=client,
        user=user3,
        group=group4,
        datasetUri=dataset1.datasetUri
    )
    # Then, userRoleForShareObject is 'NoPermission'
    assert list_dataset_share_objects_response.data.getDataset.shares.count == 2
    assert list_dataset_share_objects_response.data.getDataset.shares.nodes[0].userRoleForShareObject == 'NoPermission'


def test_list_dataset_share_objects_requesters(
        client, user2, group2, share1_draft, dataset1
):
    # Given
    # Existing share object in status Draft (->fixture share1_draft) + share object (-> fixture share)
    # When a user from the Requesters group lists the share objects for a dataset
    list_dataset_share_objects_response = list_dataset_share_objects(
        client=client,
        user=user2,
        group=group2,
        datasetUri=dataset1.datasetUri
    )
    # Then, userRoleForShareObject is 'Requesters'
    assert list_dataset_share_objects_response.data.getDataset.shares.count == 2
    assert list_dataset_share_objects_response.data.getDataset.shares.nodes[0].userRoleForShareObject == 'Requesters'


def test_list_shares_to_me_approver(
        client, user, group, share1_draft
):
    # Given
    # Existing share object in status Draft (->fixture share1_draft) + share object (-> fixture share)
    # When a user from the Approvers group lists the share objects sent to him
    get_share_requests_to_me_response = get_share_requests_to_me(client=client, user=user, group=group)
    # Then he sees the 2 shares
    assert get_share_requests_to_me_response.data.getShareRequestsToMe.count == 2


def test_list_shares_to_me_requester(
        client, user2, group2, share1_draft
):
    # Given
    # Existing share object in status Draft (->fixture share1_draft)
    # When a user from the Requesters group lists the share objects sent to him
    get_share_requests_to_me_response = get_share_requests_to_me(client=client, user=user2, group=group2)
    # Then he sees None
    assert get_share_requests_to_me_response.data.getShareRequestsToMe.count == 0


def test_list_shares_from_me_approver(
        client, user, group, share1_draft
):
    # Given
    # Existing share object in status Draft (->fixture share1_draft) + share object (-> fixture share)
    # When a user from the Approvers group lists the share objects sent from him
    get_share_requests_from_me_response = get_share_requests_from_me(client=client, user=user, group=group)
    # Then he sees None
    assert get_share_requests_from_me_response.data.getShareRequestsFromMe.count == 0


def test_list_shares_from_me_requester(
        client, user2, group2, share1_draft
):
    # Given
    # Existing share object in status Draft (->fixture share1_draft) + share object (-> fixture share)
    # When a user from the Requesters group lists the share objects sent from him
    get_share_requests_from_me_response = get_share_requests_from_me(client=client, user=user2, group=group2)
    # Then he sees the 2 shares
    assert get_share_requests_from_me_response.data.getShareRequestsFromMe.count == 2


def test_add_share_item(
        client, user2, group2, share1_draft,

):
    # Given
    # Existing share object in status Draft (-> fixture share1_draft)
    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share1_draft.shareUri,
        filter={"isShared": False}
    )
    # Given existing shareable items (-> fixture)
    shareableItem = get_share_object_response.data.getShareObject.get('items').nodes[0]
    itemUri = shareableItem['itemUri']
    itemType = shareableItem['itemType']
    shareItemUri = shareableItem['shareItemUri']
    assert shareItemUri is None

    # When we add item
    add_share_item_response = add_share_item(
        client=client,
        user=user2,
        group=group2,
        shareUri=share1_draft.shareUri,
        itemUri=itemUri,
        itemType=itemType
    )

    # Then shared item was added to share object in status PendingApproval
    assert add_share_item_response.data.addSharedItem.shareUri == share1_draft.shareUri
    assert add_share_item_response.data.addSharedItem.status == \
           dataall.api.constants.ShareItemStatus.PendingApproval.name


def test_remove_share_item(
        client, user2, group2, share1_draft, share1_item_pa
):
    # Existing share object in status Draft (-> fixture share1_draft)
    # with existing share item in status Pending Approval (-> fixture share_item_pa)
    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share1_draft.shareUri,
        filter={"isShared": True},
    )

    assert get_share_object_response.data.getShareObject.status == dataall.api.constants.ShareObjectStatus.Draft.value

    shareItem = get_share_object_response.data.getShareObject.get("items").nodes[0]
    assert shareItem.shareItemUri == share1_item_pa.shareItemUri
    assert shareItem.status == dataall.api.constants.ShareItemStatus.PendingApproval.value
    assert get_share_object_response.data.getShareObject.get("items").count == 1

    # When
    remove_share_item_response = remove_share_item(
        client=client,
        user=user2,
        group=group2,
        shareItemUri=shareItem.shareItemUri
    )

    # Then there are no more shared items added to the request
    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share1_draft.shareUri,
        filter={"isShared": True}
    )

    assert get_share_object_response.data.getShareObject.get('items').count == 0


def test_submit_share_request(
        client, user2, group2, share1_draft, share1_item_pa,
):
    # Given
    # Existing share object in status Draft (-> fixture share1_draft)
    # with existing share item in status Pending Approval (-> fixture share1_item_pa)
    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share1_draft.shareUri,
        filter={"isShared": True}
    )

    assert get_share_object_response.data.getShareObject.status == dataall.api.constants.ShareObjectStatus.Draft.value

    shareItem = get_share_object_response.data.getShareObject.get("items").nodes[0]
    assert shareItem.shareItemUri == share1_item_pa.shareItemUri
    assert shareItem.status == dataall.api.constants.ShareItemStatus.PendingApproval.value
    assert get_share_object_response.data.getShareObject.get("items").count == 1

    # When
    # Submit share object
    submit_share_object_response = submit_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share1_draft.shareUri
    )

    # Then share object status is changed to Submitted
    assert submit_share_object_response.data.submitShareObject.status == \
           dataall.api.constants.ShareObjectStatus.Submitted.name
    assert submit_share_object_response.data.submitShareObject.userRoleForShareObject == 'Requesters'

    # and share item status stays in PendingApproval
    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share1_draft.shareUri,
        filter={"isShared": True}
    )
    shareItem = get_share_object_response.data.getShareObject.get("items").nodes[0]
    status = shareItem['status']
    assert status == dataall.api.constants.ShareItemStatus.PendingApproval.name


def test_approve_share_request(
        db, client, user, group, share2_submitted, share2_item_pa
):
    # Given
    # Existing share object in status Submitted (-> fixture share2_submitted)
    # with existing share item in status Pending Approval (-> fixture share2_item_pa)
    get_share_object_response = get_share_object(
        client=client,
        user=user,
        group=group,
        shareUri=share2_submitted.shareUri,
        filter={"isShared": True}
    )

    assert get_share_object_response.data.getShareObject.status == dataall.api.constants.ShareObjectStatus.Submitted.value
    shareItem = get_share_object_response.data.getShareObject.get("items").nodes[0]
    assert shareItem.shareItemUri == share2_item_pa.shareItemUri
    assert shareItem.status == dataall.api.constants.ShareItemStatus.PendingApproval.value
    assert get_share_object_response.data.getShareObject.get("items").count == 1

    # When we approve the share object
    approve_share_object_response = approve_share_object(
        client=client,
        user=user,
        group=group,
        shareUri=share2_submitted.shareUri
    )

    # UserRole for shareObject is the Approvers in this case (user, group)
    assert approve_share_object_response.data.approveShareObject.userRoleForShareObject == 'Approvers'

    # Then share object status is changed to Approved
    assert approve_share_object_response.data.approveShareObject.status == \
           dataall.api.constants.ShareObjectStatus.Approved.name

    # and share item status is changed to Share_Approved
    get_share_object_response = get_share_object(
        client=client,
        user=user,
        group=group,
        shareUri=share2_submitted.shareUri,
        filter={"isShared": True}
    )

    shareItem = get_share_object_response.data.getShareObject.get("items").nodes[0]
    assert shareItem.status == dataall.api.constants.ShareItemStatus.Share_Approved.value

    # When approved share object is processed and the shared items successfully shared
    _successfull_processing_for_share_object(db, share2_submitted)

    get_share_object_response = get_share_object(
        client=client,
        user=user,
        group=group,
        shareUri=share2_submitted.shareUri,
        filter={"isShared": True}
    )

    # Then share object status is changed to Processed
    assert get_share_object_response.data.getShareObject.status == dataall.api.constants.ShareObjectStatus.Processed.value

    # And share item status is changed to Share_Succeeded
    shareItem = get_share_object_response.data.getShareObject.get("items").nodes[0]
    assert shareItem.status == dataall.api.constants.ShareItemStatus.Share_Succeeded.value


def test_reject_share_request(
        client, user, group, share2_submitted, share2_item_pa
):
    # Given
    # Existing share object in status Submitted (-> fixture share2_submitted)
    # with existing share item in status Pending Approval (-> fixture share2_item_pa)
    get_share_object_response = get_share_object(
        client=client,
        user=user,
        group=group,
        shareUri=share2_submitted.shareUri,
        filter={"isShared": True}
    )

    assert get_share_object_response.data.getShareObject.status == dataall.api.constants.ShareObjectStatus.Submitted.value
    shareItem = get_share_object_response.data.getShareObject.get("items").nodes[0]
    assert shareItem.shareItemUri == share2_item_pa.shareItemUri
    assert shareItem.status == dataall.api.constants.ShareItemStatus.PendingApproval.value
    assert get_share_object_response.data.getShareObject.get("items").count == 1

    # When we reject the share object
    reject_share_object_response = reject_share_object(
        client=client,
        user=user,
        group=group,
        shareUri=share2_submitted.shareUri
    )

    # Then share object status is changed to Rejected
    assert reject_share_object_response.data.rejectShareObject.status == \
           dataall.api.constants.ShareObjectStatus.Rejected.name

    # and share item status is changed to Share_Rejected
    get_share_object_response = get_share_object(
        client=client,
        user=user,
        group=group,
        shareUri=share2_submitted.shareUri,
        filter={"isShared": True}
    )

    shareItem = get_share_object_response.data.getShareObject.get("items").nodes[0]
    assert shareItem.status == dataall.api.constants.ShareItemStatus.Share_Rejected.value


def test_search_shared_items_in_environment(
        client, user2, group2, share3_processed, share3_item_shared, env2,
):
    # Given
    # Existing share object in status Processed (-> fixture share3_processed) from env2
    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share3_processed.shareUri,
        filter={"isShared": True}
    )

    assert get_share_object_response.data.getShareObject.status == dataall.api.constants.ShareObjectStatus.Processed.value

    list_datasets_published_in_environment_response = list_datasets_published_in_environment(
        client=client,
        user=user2,
        group=group2,
        environmentUri=env2.environmentUri
    )
    # Then we get the share information from the environment2
    assert list_datasets_published_in_environment_response.data.searchEnvironmentDataItems.nodes[
               0].principalId == group2.name


def test_revoke_items_share_request(
        db, client, user2, group2, share3_processed, share3_item_shared
):
    # Given
    # Existing share object in status Processed (-> fixture share3_processed)
    # with existing share item in status Share_Succeeded (-> fixture share3_item_shared)
    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share3_processed.shareUri,
        filter={"isShared": True}
    )

    assert get_share_object_response.data.getShareObject.status == dataall.api.constants.ShareObjectStatus.Processed.value

    shareItem = get_share_object_response.data.getShareObject.get("items").nodes[0]
    assert shareItem.shareItemUri == share3_item_shared.shareItemUri
    assert shareItem.status == dataall.api.constants.ShareItemStatus.Share_Succeeded.value
    revoked_items_uris = [node.shareItemUri for node in
                          get_share_object_response.data.getShareObject.get('items').nodes]

    # When
    # revoking items from share object
    revoke_items_share_object_response = revoke_items_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share3_processed.shareUri,
        revoked_items_uris=revoked_items_uris
    )
    # Then share object changes to status Rejected
    assert revoke_items_share_object_response.data.revokeItemsShareObject.status == dataall.api.constants.ShareObjectStatus.Revoked.value

    # And shared item changes to status Revoke_Approved
    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share3_processed.shareUri,
        filter={"isShared": True}
    )
    sharedItem = get_share_object_response.data.getShareObject.get('items').nodes[0]
    status = sharedItem['status']
    assert status == dataall.api.constants.ShareItemStatus.Revoke_Approved.value

    # Given the revoked share object is processed and the shared items
    # When approved share object is processed and the shared items successfully revoked (we re-use same function)
    _successfull_processing_for_share_object(db, share3_processed)

    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share3_processed.shareUri,
        filter={"isShared": True}
    )

    # Then share object status is changed to Processed
    assert get_share_object_response.data.getShareObject.status == dataall.api.constants.ShareObjectStatus.Processed.value

    # And share item status is changed to Revoke_Succeeded
    shareItem = get_share_object_response.data.getShareObject.get("items").nodes[0]
    assert shareItem.status == dataall.api.constants.ShareItemStatus.Revoke_Succeeded.value


def test_delete_share_object(
        client, user2, group2, share4_draft
):
    # Given
    # Existing share object in status Draft (-> fixture share4_draft) with no cleanup functions
    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share4_draft.shareUri,
        filter={"isShared": True}
    )

    assert get_share_object_response.data.getShareObject.status == dataall.api.constants.ShareObjectStatus.Draft.value

    # When deleting the share object
    delete_share_object_response = delete_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share4_draft.shareUri
    )
    # It is successfully deleted
    assert delete_share_object_response.data.deleteShareObject


def test_delete_share_object_remaining_items_error(
        client, user2, group2, share3_processed, share3_item_shared,
):
    # Given
    # Existing share object in status Processed (-> fixture share3_processed)
    # with existing share item in status Share_Succeeded (-> fixture share_item_shared)
    get_share_object_response = get_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share3_processed.shareUri,
        filter={"isShared": True}
    )

    assert get_share_object_response.data.getShareObject.status == dataall.api.constants.ShareObjectStatus.Processed.value

    shareItem = get_share_object_response.data.getShareObject.get("items").nodes[0]
    assert shareItem.shareItemUri == share3_item_shared.shareItemUri
    assert shareItem.status == dataall.api.constants.ShareItemStatus.Share_Succeeded.value
    assert get_share_object_response.data.getShareObject.get("items").count == 1

    # When deleting the share object
    delete_share_object_response = delete_share_object(
        client=client,
        user=user2,
        group=group2,
        shareUri=share3_processed.shareUri
    )
    # Then we get an error of the type
    assert 'UnauthorizedOperation' in delete_share_object_response.errors[0].message


def _successfull_processing_for_share_object(db, share):
    with db.scoped_session() as session:
        print('Processing share with action ShareObjectActions.Start')
        share = dataall.db.api.ShareObject.get_share_by_uri(session, share.shareUri)

        share_items_states = dataall.db.api.ShareObject.get_share_items_states(session, share.shareUri)

        Share_SM = dataall.db.api.ShareObjectSM(share.status)
        new_share_state = Share_SM.run_transition(dataall.db.models.Enums.ShareObjectActions.Start.value)

        for item_state in share_items_states:
            Item_SM = dataall.db.api.ShareItemSM(item_state)
            new_state = Item_SM.run_transition(dataall.db.models.Enums.ShareObjectActions.Start.value)
            Item_SM.update_state(session, share.shareUri, new_state)

        Share_SM.update_state(session, share, new_share_state)

        print('Processing share with action ShareObjectActions.Finish \
            and ShareItemActions.Success')

        share = dataall.db.api.ShareObject.get_share_by_uri(session, share.shareUri)
        share_items_states = dataall.db.api.ShareObject.get_share_items_states(session, share.shareUri)

        new_share_state = Share_SM.run_transition(dataall.db.models.Enums.ShareObjectActions.Finish.value)

        for item_state in share_items_states:
            Item_SM = dataall.db.api.ShareItemSM(item_state)
            new_state = Item_SM.run_transition(dataall.db.models.Enums.ShareItemActions.Success.value)
            Item_SM.update_state(session, share.shareUri, new_state)

        Share_SM.update_state(session, share, new_share_state)

