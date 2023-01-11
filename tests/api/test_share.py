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


@pytest.fixture(scope='module', autouse=True)
def org1(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module', autouse=True)
def env1(env, org1, user, group, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.check_environment', return_value=True
    )
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module')
def dataset1(db, user, env1, org1, dataset, group, group3) -> dataall.db.models.Dataset:
    with db.scoped_session() as session:
        data = dict(
            label='label',
            owner=user.userName,
            SamlAdminGroupName=group.name,
            businessOwnerDelegationEmails=['foo@amazon.com'],
            businessOwnerEmail=['bar@amazon.com'],
            name='name',
            S3BucketName='S3BucketName',
            GlueDatabaseName='GlueDatabaseName',
            KmsAlias='kmsalias',
            AwsAccountId='123456789012',
            region='eu-west-1',
            IAMDatasetAdminUserArn=f'arn:aws:iam::123456789012:user/dataset',
            IAMDatasetAdminRoleArn=f'arn:aws:iam::123456789012:role/dataset',
            stewards=group3.name,
        )
        dataset = dataall.db.api.Dataset.create_dataset(
            session=session,
            username=user.userName,
            groups=[group.name],
            uri=env1.environmentUri,
            data=data,
            check_perm=True,
        )
        yield dataset


@pytest.fixture(scope='module', autouse=True)
def tables1(table, dataset1):
    for i in range(1, 100):
        table(dataset1, name=random_table_name(), username=dataset1.owner)


@pytest.fixture(scope='module', autouse=True)
def tables1b(table, dataset1):
    for i in range(1, 100):
        table(dataset1, name=random_table_name(), username=dataset1.owner)


@pytest.fixture(scope='module')
def org2(org: typing.Callable, user2, group2, tenant) -> dataall.db.models.Organization:
    yield org('org2', user2.userName, group2.name)


@pytest.fixture(scope='module')
def env2(
        env: typing.Callable, org2: dataall.db.models.Organization, user2, group2, tenant
) -> dataall.db.models.Environment:
    yield env(org2, 'dev', user2.userName, group2.name, '2' * 12, 'eu-west-1')


@pytest.fixture(scope='module')
def dataset2(env2, org2, dataset, group2, user2) -> dataall.db.models.Dataset:
    yield dataset(
        org=org2,
        env=env2,
        name=user2.userName,
        owner=env2.owner,
        group=group2.name,
    )


@pytest.fixture(scope='module', autouse=True)
def tables2(table, dataset2):
    for i in range(1, 100):
        table(dataset2, name=random_table_name(), username=dataset2.owner)


@pytest.fixture(scope='module')
def env1group(env1):
    return env1.SamlGroupName


@pytest.fixture(scope='module')
def env2group(env1):
    return env2.SamlGroupName


@pytest.fixture(scope='module', autouse=True)
def share1(
    client, env1, user, env1group, dataset2
):
    q = """
    mutation CreateShareObject(
        $datasetUri:String!,
        $input:NewShareObjectInput
    ){
        createShareObject(datasetUri:$datasetUri, input:$input){
            shareUri
            status
            owner
            dataset{
                datasetUri
                datasetName
                exists
            }
        }
    }
    """

    response = client.query(
        q,
        username=user.userName,
        groups=[env1group],
        datasetUri=dataset2.datasetUri,
        input={
            'environmentUri': env1.environmentUri,
            'groupUri': env1group,
            'principalId': env1group,
            'principalType': dataall.api.constants.PrincipalType.Group.name,
        },
    )
    return response.data.createShareObject


@pytest.fixture(scope='module', autouse=True)
def share2_with_items(
    client, env2, user2, env2group, dataset1
):
    q = """
    mutation CreateShareObject(
        $datasetUri:String!,
        $input:NewShareObjectInput
    ){
        createShareObject(datasetUri:$datasetUri, input:$input){
            shareUri
            status
            owner
            dataset{
                datasetUri
                datasetName
                exists
            }
        }
    }
    """

    response = client.query(
        q,
        username=user2.userName,
        groups=[env2group],
        datasetUri=dataset1.datasetUri,
        input={
            'environmentUri': env2.environmentUri,
            'groupUri': env2group,
            'principalId': env2group,
            'principalType': dataall.api.constants.PrincipalType.Group.name,
        },
    )

    # Add share item
    addSharedItemQuery = """
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
        addSharedItemQuery,
        username=user2.userName,
        groups=[env2group],
        shareUri=response.data.createShareObject.shareUri,
        input={
            'itemUri': tables1[0].tableUri,
            'itemType': dataall.api.constants.ShareableType.Table.value,
        },
    )
    # And item has been added to the share request
    getShareObjectQuery = """
        query getShareObject($shareUri: String!, $filter: ShareableObjectFilter) {
          getShareObject(shareUri: $shareUri) {
            shareUri
            created
            owner
            status
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
          }
        }
    """

    response = client.query(
        getShareObjectQuery,
        username=user2.userName,
        groups=[env2group],
        shareUri=response.data.createShareObject.shareUri,
        filter={},
    )

    return response.data.getShareObject


def test_init(tables1, tables1b, tables2):
    assert True


def test_create_share_object_unauthorized(client, dataset1, env2, group2, group3):
    """
    Test a user that opens a share request for a group that he does not belong to. It is prevented in the frontend (client side)
    but here we are checking that it is also unauthorized in the server side.
    """

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
        }
      }
    """

    response = client.query(
        q,
        username='anonymous',
        groups=[group3.name],
        datasetUri=dataset1.datasetUri,
        input={
            'environmentUri': env2.environmentUri,
            'groupUri': group2.name,
            'principalId': group2.groupUri,
            'principalType': dataall.api.constants.PrincipalType.Group.name,
        },
    )

    assert 'Unauthorized' in response.errors[0].message


def test_create_share_object_authorized(client, dataset1, env2, db, user2,
                                        group2, env1):
    """
    Tests a share that has been created successfully. Dataset admins are not requesters.
    """
    # Given
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

    # When
    response = client.query(
        q,
        username=user2.userName,
        groups=[group2.name],
        datasetUri=dataset1.datasetUri,
        input={
            'environmentUri': env2.environmentUri,
            'groupUri': group2.name,
            'principalId': group2.name,
            'principalType': dataall.api.constants.PrincipalType.Group.name,
        },
    )

    # Then share object created with status Draft
    print('Create share request response: ', response.data.createShareObject)
    assert response.data.createShareObject.shareUri
    assert response.data.createShareObject.status == dataall.api.constants.ShareObjectStatus.Draft.name
    assert response.data.createShareObject.userRoleForShareObject == 'Requesters'


def test_create_share_object_with_item_authorized(client, dataset1, env2, db, user2,
                                        group2, env1, tables1):
    """
    Tests a share that has been created successfully. Dataset admins are not requesters.
    :param client:
    :param dataset1:
    :param env2:
    :param db:
    :param user2:
    :param group2:
    :param env1:
    :return:
    """
    # Given
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

    # When
    response = client.query(
        q,
        username=user2.userName,
        groups=[group2.name],
        datasetUri=dataset1.datasetUri,
        itemType=dataall.api.constants.ShareableType.Table.value,
        itemUri=tables1[0].tableUri,
        input={
            'environmentUri': env2.environmentUri,
            'groupUri': group2.name,
            'principalId': group2.name,
            'principalType': dataall.api.constants.PrincipalType.Group.name,
        },
    )

    # Then share object created with status Draft
    print('Create share request response: ', response.data.createShareObject)
    assert response.data.createShareObject.shareUri
    assert response.data.createShareObject.status == dataall.api.constants.ShareObjectStatus.Draft.name
    assert response.data.createShareObject.userRoleForShareObject == 'Requesters'

    # And item has been added to the share request
    q = """
        query getShareObject($shareUri: String!, $filter: ShareableObjectFilter) {
          getShareObject(shareUri: $shareUri) {
            shareUri
            created
            owner
            status
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
          }
        }
    """

    response2 = client.query(
        q,
        username=user2.userName,
        groups=[group2.name],
        shareUri=response.data.createShareObject.shareUri,
        filter={},
    )
    print(response2)
    assert response2.data.getShareObject.items.nodes[0].itemUri == tables1.tableUri
    assert response2.data.getShareObject.items.nodes[0].itemType == dataall.api.constants.ShareableType.Table.value


def test_get_share_object(client, share1, user, env1group):
    """
    test get share object
    """
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
        groups=[env1group],
        shareUri=share1.shareUri,
        filter={},
    )
    print(response)
    assert response.data.getShareObject.shareUri == share1.shareUri
    assert response.data.getShareObject.principal.principalType == \
        dataall.api.constants.PrincipalType.Group.name
    assert response.data.getShareObject.principal.principalIAMRoleName
    assert response.data.getShareObject.principal.SamlGroupName
    assert response.data.getShareObject.principal.region


def test_list_dataset_share_objects(
        client, dataset1, env1, user, user3, env2, db, user2, group2, group, group4
):
    """
    Test listing shares from dataset shares tab
    """
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
        datasetUri=dataset1.datasetUri,
    )

    assert response.data.getDataset.shares.count >= 1
    assert (
            response.data.getDataset.shares.nodes[0].userRoleForShareObject == 'Requesters'
    )

    response = client.query(
        q, username=user3.userName, groups=[group4.name], datasetUri=dataset1.datasetUri
    )

    assert response.data.getDataset.shares.count == 1
    assert (
            response.data.getDataset.shares.nodes[0].userRoleForShareObject
            == 'NoPermission'
    )

    response = client.query(
        q,
        username=user2.userName,
        groups=[dataset1.SamlAdminGroupName],
        datasetUri=dataset1.datasetUri,
    )
    assert response.data.getDataset.shares.count == 1
    assert (
            response.data.getDataset.shares.nodes[0].userRoleForShareObject == 'Requesters'
    )


def test_add_shared_item(
        share1,
        tables2,
        client,
        user,
        group
):
    # Given existing share object in status Draft (-> fixture)
    getShareObjectQuery = """
        query getShareObject($shareUri: String!) {
              getShareObject(shareUri: $shareUri) {
                shareUri
                created
                owner
                status
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
        getShareObjectQuery,
        username=user.userName,
        shareUri=share1.shareUri,
        groups=[group.name],
    )

    print('Response from getShareObject: ', response)

    assert (
        response.data.getShareObject.status
        == dataall.api.constants.ShareObjectStatus.Draft.name
    )

    # Given existing shareable items (-> fixture)
    shareableItem = response.data.getShareObject.get('items').nodes[0]
    itemUri = shareableItem['itemUri']
    itemType = shareableItem['itemType']
    shareItemUri = shareableItem['shareItemUri']
    assert shareItemUri is None

    # When
    addSharedItemQuery = """
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
        addSharedItemQuery,
        username=user.userName,
        groups=[group.name],
        shareUri=share1.shareUri,
        input={
            'itemUri': itemUri,
            'itemType': itemType,
        },
    )

    print('Response from addSharedItem: ', response)

    # Then shared item was added to share object in status PendingApproval
    assert response.data.addSharedItem.shareUri == share1.shareUri
    assert response.data.addSharedItem.status == \
        dataall.api.constants.ShareItemStatus.PendingApproval.name


def test_remove_shared_item(
        share2,
        tables1,
        client,
        user2,
        env2group
):
    # Given existing share object in status Draft with one share item (-> fixture)
    getShareObjectQuery = """
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
        getShareObjectQuery,
        username=user2.userName,
        shareUri=share2_with_items.shareUri,
        filter={"isShared": True},
        groups=[env2group],
    )

    print('Response from getShareObject: ', response)

    assert (
        response.data.getShareObject.status
        == dataall.api.constants.ShareObjectStatus.Draft.name
    )

    # Given existing pendingapproval added item (-> fixture)
    shareItem = response.data.getShareObject.get('items').nodes[0]
    assert shareItem.shareItemUri is not None
    assert shareItem.status == dataall.api.constants.ShareItemStatus.PendingApproval.name


    # When
    removeSharedItemQuery = """
    mutation RemoveSharedItem($shareItemUri: String!) {
      removeSharedItem(shareItemUri: $shareItemUri)
    }
    """

    response = client.query(
        removeSharedItemQuery,
        username=user2.userName,
        groups=[env2group],
        shareItemUri=shareItem.shareItemUri
    )

    print('Response from removeSharedItem: ', response)

    # Then shared item was added to share object in status PendingApproval
    #TODO


@pytest.mark.dependency(depends=["test_add_shared_item"])
def test_submit_share_request(
        share1,
        client,
        user,
        group
):

    # Given existing share object in status Draft (-> fixture)
    getShareObjectQuery = """
        query getShareObject($shareUri: String!) {
              getShareObject(shareUri: $shareUri) {
                shareUri
                created
                owner
                status
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
        getShareObjectQuery,
        username=user.userName,
        shareUri=share1.shareUri,
        groups=[group.name],
    )

    print('Response from getShareObject: ', response)

    # When submit share object
    query = """
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
        query,
        username=user.userName,
        shareUri=share1.shareUri,
        groups=[group.name],
    )

    # Then share object status is changed to Submitted
    assert response.data.submitShareObject.status == \
        dataall.api.constants.ShareObjectStatus.Submitted.name
    assert response.data.submitShareObject.userRoleForShareObject == 'Requesters'

    # Then shared item status stays in PendingApproval
    sharedItem = response.data.submitShareObject.get('items').nodes[0]
    status = sharedItem['status']
    status == dataall.api.constants.ShareItemStatus.PendingApproval.name


@pytest.mark.dependency(depends=["test_submit_share_request"])
def test_approve_share_object(
        share1,
        user2,
        group2,
        client,
        env2,
        org2,
        user,
        group3,
        user3,
        module_mocker,
        group,
):

    # Given existing share object in status  (-> Submitted)
    getShareObjectQuery = """
        query getShareObject($shareUri: String!) {
              getShareObject(shareUri: $shareUri) {
                shareUri
                created
                owner
                status
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
        getShareObjectQuery,
        username=user2.userName,
        shareUri=share1.shareUri,
        groups=[group2.name],
    )

    print('Response from getShareObject: ', response)

    query = """
            mutation approveShareObject($shareUri:String!){
                approveShareObject(shareUri:$shareUri){
                    status
                    owner
                    userRoleForShareObject
                }
            }
            """

    response = client.query(
        query,
        username=user2.userName,
        shareUri=share1.shareUri,
        groups=[group2.name],
    )
    assert response.data.approveShareObject.status == 'Approved'
    assert response.data.approveShareObject.userRoleForShareObject == 'Approvers'


@pytest.mark.dependency(depends=["test_approve_share_request"])
def test_search_shared_items_in_environment(
        client,
        user2,
        env2,
        group2
):
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
        username=user2.userName,
        groups=[env2.SamlGroupName],
        environmentUri=env2.environmentUri,
        filter={'itemTypes': 'DatasetTable'},
    )
    assert response.data.searchEnvironmentDataItems.nodes[0].principalId == group2.name

#TODO: add and remove
def test_revoke_shared_item(
        share1,
        tables2,
        client,
        user,
        group
):
    # Given existing share object in status Draft (-> fixture)
    getShareObjectQuery = """
        query getShareObject($shareUri: String!) {
              getShareObject(shareUri: $shareUri) {
                shareUri
                created
                owner
                status
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
        getShareObjectQuery,
        username=user.userName,
        shareUri=share1.shareUri,
        groups=[group.name],
    )

    print('Response from getShareObject: ', response)

    assert (
        response.data.getShareObject.status
        == dataall.api.constants.ShareObjectStatus.Draft.name
    )

    # Given existing shareable items (-> fixture)
    shareableItem = response.data.getShareObject.get('items').nodes[0]
    itemUri = shareableItem['itemUri']
    itemType = shareableItem['itemType']
    shareItemUri = shareableItem['shareItemUri']
    assert shareItemUri is None

    # When
    addSharedItemQuery = """
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
        addSharedItemQuery,
        username=user.userName,
        groups=[group.name],
        shareUri=share1.shareUri,
        input={
            'itemUri': itemUri,
            'itemType': itemType,
        },
    )

    print('Repsonse from addSharedItem: ', response)

    # Then shared item was added to share object in status PendingApproval
    assert response.data.addSharedItem.shareUri == share1.shareUri
    assert response.data.addSharedItem.status == \
        dataall.api.constants.ShareItemStatus.PendingApproval.name


@pytest.mark.dependency(depends=["test_approve_share_object"])
def test_revoke_all_share_object_completed(
        share1,
        user2,
        group2,
        client,
        db
):

    # Given the approved share object is processed and the shared items
    # are succesfully shared
    succesfull_processing_for_approved_share_object(db, share1)

    # Given existing share object in status Completed
    getShareObjectQuery = """
        query getShareObject($shareUri: String!) {
              getShareObject(shareUri: $shareUri) {
                shareUri
                created
                owner
                status
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
        getShareObjectQuery,
        username=user2.userName,
        shareUri=share1.shareUri,
        groups=[group2.name],
    )

    print('Response from getShareObject: ', response)

    assert (
        response.data.getShareObject.status
        == dataall.api.constants.ShareObjectStatus.Completed.name
    )

    # Given shared item in status Share_Succeeded
    sharedItem = response.data.getShareObject.get('items').nodes[0]
    assert sharedItem['status'] == dataall.api.constants.ShareItemStatus.Share_Succeeded.name

    # When revoking all share object
    query = """
                mutation revokeAllShareObject($shareUri:String!){
                    revokeAllShareObject(shareUri:$shareUri){
                        shareUri
                        status
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
        query,
        username=user2.userName,
        shareUri=share1.shareUri,
        groups=[group2.name],
    )

    # Then share object changes to status Rejected
    assert response.data.revokeAllShareObject.status == 'Rejected'

    # Then shared item changes to status Revoke_Approved
    sharedItem = response.data.revokeAllShareObject.get('items').nodes[0]
    status = sharedItem['status']
    status == dataall.api.constants.ShareItemStatus.Revoke_Approved.name
    # query = """
    #     mutation RemoveSharedItem($shareItemUri:String!){
    #         removeSharedItem(shareItemUri:$shareItemUri)
    #     }
    #     """
    # response = client.query(
    #     query,
    #     username=user2.owner,
    #     groups=[group2.name],
    #     shareItemUri=share_item_uri,
    # )

    # assert response.data.removeSharedItem
    # received_requests = """
    #         query getShareRequestsToMe($filter: ShareObjectFilter){
    #             getShareRequestsToMe(filter: $filter){
    #                 count
    #                 nodes{
    #                     shareUri
    #                 }
    #             }
    #         }
    # """
    # response = client.query(
    #     received_requests, username=user.userName, groups=[group.name]
    # )
    # assert response.data.getShareRequestsToMe.count == 0
    # received_requests = """
    #             query getShareRequestsToMe($filter: ShareObjectFilter){
    #                 getShareRequestsToMe(filter: $filter){
    #                     count
    #                     nod es{
    #                         shareUri
    #                     }
    #                 }
    #             }
    #     """
    # response = client.query(
    #     received_requests, username=user3.userName, groups=[group3.name]
    # )
    # assert response.data.getShareRequestsToMe.count == 1

    # sent_requests = """
    #                 query getShareRequestsFromMe($filter: ShareObjectFilter){
    #                     getShareRequestsFromMe(filter: $filter){
    #                         count
    #                         nodes{
    #                             shareUri
     #                         }
    #                     }
    #                 }
    #         """
    # response = client.query(
    #     sent_requests, username=user2.userName, groups=[group2.name]
    # )
    # assert response.data.getShareRequestsFromMe.count == 1

    # sent_requests = """
    #                     query getShareRequestsFromMe($filter: ShareObjectFilter){
    #                         getShareRequestsFromMe(filter: $filter){
    #                             count
    #                             nodes{
    #                                 shareUri
    #                             }
    #                         }
    #                     }
    #             """
    # response = client.query(
    #     sent_requests, username=user3.userName, groups=[group3.name]
    # )
    # assert response.data.getShareRequestsFromMe.count == 0


# def test_notifications(client, db, user):
#     list = """
#                 query ListNotifications{
#                     listNotifications{
#                         count
#                         nodes{
#                             notificationUri
#                             message
#                             type
#                             is_read
#                         }
#                     }
#                 }
#                 """
#     response = client.query(list, username=user.userName)
#     assert (
#         response.data.listNotifications.nodes[0].type
#         == dataall.db.models.NotificationType.SHARE_OBJECT_SUBMITTED.name
#     )
#     notificationUri = response.data.listNotifications.nodes[0].notificationUri
#     query = """
#                 query CountUnread{
#                     countUnreadNotifications
#                 }
#                 """
#     response = client.query(query, username=user.userName)
#     assert response.data.countUnreadNotifications == 3
#     read = """
#             mutation markAsRead($notificationUri:String!){
#                 markNotificationAsRead(notificationUri:$notificationUri)
#             }
#             """
#     response = client.query(
#         read, username=user.userName, notificationUri=notificationUri
#     )
#     assert response

#     query = """
#                     query countReadNotifications{
#                         countReadNotifications
#                     }
#                     """
#     response = client.query(query, username=user.userName)
#     assert response.data.countReadNotifications == 1
#     read = """
#                 mutation deleteNotification($notificationUri:String!){
#                     deleteNotification(notificationUri:$notificationUri)
#                 }
#                 """
#     response = client.query(
#         read, username=user.userName, notificationUri=notificationUri
#     )
#     assert response
#     query = """
#                         query countDeletedNotifications{
#                             countDeletedNotifications
#                         }
#                         """
#     response = client.query(query, username=user.userName)
#     assert response.data.countDeletedNotifications == 1

#     query = """
#             query ListNotifications($filter:NotificationFilter){
#                     listNotifications(filter:$filter){
#                         count
#                         nodes{
#                             notificationUri
#                             message
#                             type
#                             is_read
#                         }
#                     }
#                 }
#     """
#     response = client.query(
#         query, username=user.userName, filter={'unread': True})
#     assert response.data.listNotifications.count == 2

#     query = """
#                 query ListNotifications($filter:NotificationFilter){
#                         listNotifications(filter:$filter){
#                             count
#                             nodes{
#                                 notificationUri
#                                 message
#                                 type
#                                 is_read
#                             }
#                         }
#                     }
#         """
#     response = client.query(
#         query, username=user.userName, filter={'read': True})
#     assert response.data.listNotifications.count == 0

#     query = """
#                     query ListNotifications($filter:NotificationFilter){
#                             listNotifications(filter:$filter){
#                                 count
#                                 nodes{
#                                     notificationUri
#                                     message
#                                     type
#                                     is_read
#                                 }
#                             }
#                         }
#             """
#     response = client.query(query, username=user.userName,
#                             filter={'archived': True})
#     assert response.data.listNotifications.count == 1


# def test_delete_share_object(client, dataset1, group, user2, group2, env2):
#     get_share_object_query = """
#     query GetDataset(
#         $datasetUri:String!,
#     ){
#         getDataset(datasetUri:$datasetUri){
#             datasetUri
#             tables{
#                 count
#                 nodes{
#                     tableUri

#                 }

#             }
#             shares{
#                 count
#                 nodes{
#                     owner
#                     shareUri
#                     status

#                 }
#             }
#         }
#     }
#     """
#     response = client.query(
#         get_share_object_query,
#         username=dataset1.owner,
#         groups=[group.name],
#         datasetUri=dataset1.datasetUri,
#     )
#     share_object = response.data.getDataset.shares.nodes[0]

#     delete_share_object_query = """
#     mutation DeleteShareObject($shareUri: String!){
#       deleteShareObject(shareUri:$shareUri)
#     }
#     """
#     response = client.query(
#         delete_share_object_query,
#         username=dataset1.owner,
#         groups=[group.name],
#         shareUri=share_object.shareUri,
#     )
#     assert response.data.deleteShareObject

#     create_shared_object_query = """
#       mutation CreateShareObject(
#         $datasetUri: String!
#         $itemType: String
#         $itemUri: String
#         $input: NewShareObjectInput
#       ) {
#         createShareObject(
#           datasetUri: $datasetUri
#           itemType: $itemType
#           itemUri: $itemUri
#           input: $input
#         ) {
#           shareUri
#           created
#         }
#       }
#     """

#     client.query(
#         create_shared_object_query,
#         username=user2.userName,
#         groups=[group2.name],
#         datasetUri=dataset1.datasetUri,
#         input={
#             'environmentUri': env2.environmentUri,
#             'groupUri': group2.name,
#             'principalId': group2.name,
#             'principalType': dataall.api.constants.PrincipalType.Group.name,
#         },
#     )

#     add_item_query = """
#     mutation AddSharedItem($shareUri:String!,$input:AddSharedItemInput){
#         addSharedItem(shareUri:$shareUri,input:$input){
#             shareUri
#             shareItemUri
#             itemUri
#         }
#     }
#     """
#     response = client.query(
#         get_share_object_query,
#         username=dataset1.owner,
#         groups=[group.name],
#         datasetUri=dataset1.datasetUri,
#     )

#     share_object = response.data.getDataset.shares.nodes[0]

#     this_dataset_tables = response.data.getDataset.tables.nodes
#     random_table: dataall.db.models.DatasetTable = random.choice(
#         this_dataset_tables)
#     response = client.query(
#         add_item_query,
#         username=share_object.owner,
#         groups=[group2.name],
#         shareUri=share_object.shareUri,
#         input={
#             'itemUri': random_table.tableUri,
#             'itemType': dataall.api.constants.ShareableType.Table.name,
#         },
#     )

#     shared_item = response.data.addSharedItem

#     response = client.query(
#         delete_share_object_query,
#         username=user2.userName, groups=[group2.name],
#         shareUri=share_object.shareUri,
#     )
#     assert 'ShareItemsFound' in response.errors[0].message

#     remove_item_query = """
#         mutation RemoveSharedItem($shareItemUri:String!){
#             removeSharedItem(shareItemUri:$shareItemUri)
#         }
#     """
#     client.query(
#         remove_item_query,
#         username=user2.userName,
#         groups=[group2.name],
#         shareItemUri=shared_item.shareItemUri
#     )

#     response = client.query(
#         delete_share_object_query,
#         username=user2.userName, groups=[group2.name],
#         shareUri=share_object.shareUri,
#     )
#     assert response.data.deleteShareObject


def succesfull_processing_for_approved_share_object(db, share):
    with db.scoped_session() as session:
        print('Processing approved share with action ShareObjectActions.Start')
        share = dataall.db.api.ShareObject.get_share_by_uri(session, share.shareUri)

        share_items_states = dataall.db.api.ShareObject.get_share_items_states(session, share.shareUri)

        Share_SM = dataall.db.api.ShareObjectSM(share.status)
        new_share_state = Share_SM.run_transition(dataall.db.models.Enums.ShareObjectActions.Start.value)

        for item_state in share_items_states:
            Item_SM = dataall.db.api.ShareItemSM(item_state)
            new_state = Item_SM.run_transition(dataall.db.models.Enums.ShareObjectActions.Start.value)
            Item_SM.update_state(session, share.shareUri, new_state)

        Share_SM.update_state(session, share, new_share_state)

        print('Processing approved share with action ShareObjectActions.Finish \
            and ShareItemActions.Success')

        share = dataall.db.api.ShareObject.get_share_by_uri(session, share.shareUri)
        share_items_states = dataall.db.api.ShareObject.get_share_items_states(session, share.shareUri)

        new_share_state = Share_SM.run_transition(dataall.db.models.Enums.ShareObjectActions.Finish.value)

        for item_state in share_items_states:
            Item_SM = dataall.db.api.ShareItemSM(item_state)
            new_state = Item_SM.run_transition(dataall.db.models.Enums.ShareItemActions.Success.value)
            Item_SM.update_state(session, share.shareUri, new_state)

        Share_SM.update_state(session, share, new_share_state)
