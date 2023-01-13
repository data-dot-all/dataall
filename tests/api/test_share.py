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

# @pytest.fixture(scope='module')
# def dataset1(db, user, env1, org1, dataset, group, group3) -> dataall.db.models.Dataset:
#     with db.scoped_session() as session:
#         data = dict(
#             label='label',
#             owner=user.userName,
#             SamlAdminGroupName=group.name,
#             businessOwnerDelegationEmails=['foo@amazon.com'],
#             businessOwnerEmail=['bar@amazon.com'],
#             name='name',
#             S3BucketName='S3BucketName',
#             GlueDatabaseName='GlueDatabaseName',
#             KmsAlias='kmsalias',
#             AwsAccountId='123456789012',
#             region='eu-west-1',
#             IAMDatasetAdminUserArn=f'arn:aws:iam::123456789012:user/dataset',
#             IAMDatasetAdminRoleArn=f'arn:aws:iam::123456789012:role/dataset',
#             stewards=group3.name,
#         )
#         dataset = dataall.db.api.Dataset.create_dataset(
#             session=session,
#             username=user.userName,
#             groups=[group.name],
#             uri=env1.environmentUri,
#             data=data,
#             check_perm=True,
#         )
#         yield dataset


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
def table1(table: typing.Callable, dataset1: dataall.db.models.Dataset, user: dataall.db.models.User) -> dataall.db.models.DatasetTable:
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
def table2(table: typing.Callable, dataset2: dataall.db.models.Dataset, user2: dataall.db.models.User) -> dataall.db.models.DatasetTable:
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



@pytest.fixture(scope='module')
def share1(
        share: typing.Callable,
        dataset1: dataall.db.models.Dataset,
        env2: dataall.db.models.Environment,
        env2group: dataall.db.models.EnvironmentGroup,
        user2: dataall.db.models.User
) -> dataall.db.models.ShareObject:
    yield share(
        dataset=dataset1,
        environment=env2,
        env_group=env2group,
        owner=user2.userName,
        status=dataall.api.constants.ShareObjectStatus.Draft.value
    )


@pytest.fixture(scope='module')
def share2(
        share: typing.Callable,
        dataset2: dataall.db.models.Dataset,
        env1: dataall.db.models.Environment,
        env1group: dataall.db.models.EnvironmentGroup,
        user: dataall.db.models.User
) -> dataall.db.models.ShareObject:
    yield share(
        dataset=dataset2,
        environment=env1,
        env_group=env1group,
        owner=user.userName,
        status=dataall.api.constants.ShareObjectStatus.Draft.value
    )


@pytest.fixture(scope='module')
def share_item2_pa(
        share_item: typing.Callable,
        share2: dataall.db.models.ShareObject,
        table2: dataall.db.models.DatasetTable
) -> dataall.db.models.ShareObjectItem:
    yield share_item(
        share=share2,
        table=table2,
        status=dataall.api.constants.ShareItemStatus.PendingApproval.value
    )


@pytest.fixture(scope='module')
def share_item2_shared(
        share_item: typing.Callable,
        share2: dataall.db.models.ShareObject,
        table2: dataall.db.models.DatasetTable
) -> dataall.db.models.ShareObjectItem:
    yield share_item(
        share=share2,
        table=table2,
        status=dataall.api.constants.ShareItemStatus.Share_Succeeded.value
    )


def test_init(tables1, tables2):
    assert True


def test_create_share_object_unauthorized(client, dataset1, env2, group2, env2group, group3):
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
            'groupUri': env2group.groupUri,
            'principalId': env2group.groupUri,
            'principalType': dataall.api.constants.PrincipalType.Group.value,
        },
    )

    assert 'Unauthorized' in response.errors[0].message


@pytest.mark.dependency()
def test_create_share_object_authorized(client, dataset1, env2, db, user2,
                                        group2, env2group, env1):
    """
    Tests a share that has been created successfully. Dataset admins are not requesters.
    Request is created by requesting a dataset.
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
            'groupUri': env2group.groupUri,
            'principalId': env2group.groupUri,
            'principalType': dataall.api.constants.PrincipalType.Group.value,
        },
    )

    # Then share object created with status Draft
    print('Create share request response: ', response.data.createShareObject)
    assert response.data.createShareObject.shareUri
    assert response.data.createShareObject.status == dataall.api.constants.ShareObjectStatus.Draft.value
    assert response.data.createShareObject.userRoleForShareObject == 'Requesters'


def test_create_share_object_with_item_authorized(client, dataset1, env2, db, user2,
                                        group2, env2group, env1, table1):
    """
    Tests a share that has been created successfully. Dataset admins are not requesters.
    Request is created by requesting a folder or a table.
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
        itemUri=table1.tableUri,
        input={
            'environmentUri': env2.environmentUri,
            'groupUri': env2group.groupUri,
            'principalId': env2group.groupUri,
            'principalType': dataall.api.constants.PrincipalType.Group.value,
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
        filter={"isShared": True},
    )
    print('Get share request response: ', response2.data.getShareObject)
    assert response2.data.getShareObject.get('items').nodes[0].itemUri == table1.tableUri
    assert response2.data.getShareObject.get('items').nodes[0].itemType == dataall.api.constants.ShareableType.Table.name


def test_get_share_object(client, share1, user, group):
    """
    test get share object. Share object with permissions created in fixture.
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
        groups=[group.name],
        shareUri=share1.shareUri,
        filter={},
    )
    print(response)
    assert response.data.getShareObject.shareUri == share1.shareUri
    assert response.data.getShareObject.get('principal').principalType == dataall.api.constants.PrincipalType.Group.name
    assert response.data.getShareObject.get('principal').principalIAMRoleName
    assert response.data.getShareObject.get('principal').SamlGroupName
    assert response.data.getShareObject.get('principal').region


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

    assert response.data.getDataset.shares.count == 2
    assert (
            response.data.getDataset.shares.nodes[0].userRoleForShareObject == 'Approvers'
    )

    response = client.query(
        q,
        username=user3.userName,
        groups=[group4.name],
        datasetUri=dataset1.datasetUri
    )

    assert response.data.getDataset.shares.count == 2
    assert (
            response.data.getDataset.shares.nodes[0].userRoleForShareObject
            == 'NoPermission'
    )

    response = client.query(
        q,
        username=user2.userName,
        groups=[group2.name],
        datasetUri=dataset1.datasetUri,
    )
    assert response.data.getDataset.shares.count == 2
    assert (
            response.data.getDataset.shares.nodes[0].userRoleForShareObject == 'Requesters'
    )


@pytest.mark.dependency(depends=["test_create_share_object_authorized"])
def test_list_shares_to_me(
        client,
        user,
        group,
        user2,
        group2
):
    """
    Test listing shares in your inbox. Group 2 are requesters, group 1 are approvers
    """
    getShareRequestsToMeQuery = """
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
        getShareRequestsToMeQuery,
        username=user.userName,
        groups=[group.name]
    )
    assert response.data.getShareRequestsToMe.count == 2

    response = client.query(
        getShareRequestsToMeQuery,
        username=user2.userName,
        groups=[group2.name]
    )
    assert response.data.getShareRequestsToMe.count == 0


@pytest.mark.dependency(depends=["test_create_share_object_authorized"])
def test_list_shares_from_me(
        client,
        user,
        group,
        user2,
        group2
):
    """
    Test listing shares in your outbox. Group 2 are requesters, group 1 are approvers
    """
    getShareRequestsFromMeQuery = """
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
        getShareRequestsFromMeQuery,
        username=user2.userName,
        groups=[group2.name]
    )
    assert response.data.getShareRequestsFromMe.count == 2

    response = client.query(
        getShareRequestsFromMeQuery,
        username=user.userName,
        groups=[group.name]
    )
    assert response.data.getShareRequestsFromMe.count == 0

@pytest.mark.dependency()
def test_add_share_item(
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


@pytest.mark.dependency(depends=["test_add_share_item"])
def test_submit_share_request(
        share1,
        client,
        user2,
        group2
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
        username=user2.userName,
        shareUri=share1.shareUri,
        groups=[group2.name],
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
        username=user2.userName,
        shareUri=share1.shareUri,
        groups=[group2.name],
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
def test_approve_share_request(
        share1,
        client,
        user,
        group,
        db
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
        username=user.userName,
        shareUri=share1.shareUri,
        groups=[group.name],
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
        username=user.userName,
        shareUri=share1.shareUri,
        groups=[group.name],
    )
    assert response.data.approveShareObject.status == \
           dataall.api.constants.ShareObjectStatus.Approved.name
    assert response.data.approveShareObject.userRoleForShareObject == 'Approvers'

    # Given the approved share object is processed and the shared items
    # are successfully shared
    _successfull_processing_for_approved_share_object(db, share1)


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
        groups=[group2.name],
        environmentUri=env2.environmentUri,
        filter={},
    )
    print("searchEnvironmentDataItems response: ", response.data.searchEnvironmentDataItems)
    assert response.data.searchEnvironmentDataItems.nodes[0].principalId == group2.name


@pytest.mark.dependency(depends=["test_approve_share_request"])
def test_revoke_all_share_request_completed(
        client,
        share1,
        user2,
        group2,
        db
):

    # Given existing share object in status Completed
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
        shareUri=share1.shareUri,
        groups=[group2.name],
    )

    print('Response from getShareObject: ', response)

    assert (
        response.data.getShareObject.status
        == dataall.api.constants.ShareObjectStatus.Completed.value
    )

    # Given shared item in status Share_Succeeded
    sharedItem = response.data.getShareObject.get('items').nodes[0]
    assert sharedItem['status'] == dataall.api.constants.ShareItemStatus.Share_Succeeded.value

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
        filter={"isShared": True},
        groups=[group2.name],
    )

    # Then share object changes to status Rejected
    assert response.data.revokeAllShareObject.status == 'Rejected'

    # Then shared item changes to status Revoke_Approved
    sharedItem = response.data.revokeAllShareObject.get('items').nodes[0]
    status = sharedItem['status']
    status == dataall.api.constants.ShareItemStatus.Revoke_Approved.value

    # Given the revoked share object is processed and the shared items
    # are successfully revoked. We can re-use the same successful processing function
    _successfull_processing_for_approved_share_object(db, share1)


@pytest.mark.dependency(depends=["test_revoke_all_share_request_completed"])
def test_delete_share_object(client, share1, dataset1, group, user2, group2, env2):
    # Given existing share object in status Rejected (-> fixture)
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
        shareUri=share1.shareUri,
        filter={"isShared": True},
        groups=[group2.name],
    )

    print('Response from getShareObject: ', response)

    # When deleting the share object
    DeleteShareObjectQuery = """
        mutation DeleteShareObject($shareUri: String!){
          deleteShareObject(shareUri:$shareUri)
        }
    """
    response = client.query(
        DeleteShareObjectQuery,
        username=user2.userName,
        groups=[group2.name],
        shareUri=share1.shareUri,
    )
    # It is successfully deleted
    assert response.data.deleteShareObject


@pytest.mark.dependency()
def test_remove_share_item(
        share2,
        share_item2_pa,
        client,
        user2,
        group2
):
    # Given existing share object in status Draft with 2 share items (-> fixture)
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
        shareUri=share2.shareUri,
        filter={"isShared": True},
        groups=[group2.name],
    )

    print('Response from getShareObject: ', response)

    assert (
        response.data.getShareObject.status
        == dataall.api.constants.ShareObjectStatus.Draft.name
    )

    # Given existing pendingapproval added items (-> fixture)
    shareItem = response.data.getShareObject.get('items').nodes[0]
    assert shareItem.shareItemUri == share_item2_pa.shareItemUri
    assert shareItem.status == dataall.api.constants.ShareItemStatus.PendingApproval.value
    assert response.data.getShareObject.get('items').count == 1

    # When
    removeSharedItemQuery = """
    mutation RemoveSharedItem($shareItemUri: String!) {
      removeSharedItem(shareItemUri: $shareItemUri)
    }
    """

    response = client.query(
        removeSharedItemQuery,
        username=user2.userName,
        groups=[group2.name],
        shareItemUri=shareItem.shareItemUri
    )

    print('Response from removeSharedItem: ', response)

    # Then there are no more shared items added to the request
    response = client.query(
        getShareObjectQuery,
        username=user2.userName,
        shareUri=share2.shareUri,
        filter={"isShared": True},
        groups=[group2.name],
    )

    print('Response from getShareObject: ', response)
    assert response.data.getShareObject.get('items').count == 0



@pytest.mark.dependency(depends=["test_remove_share_item"])
def test_delete_share_object_remaining_items_error(
        client,
        share2,
        share_item2_shared,
        dataset1,
        user,
        group,
        env2
):
    # Given existing share object in status Rejected (-> fixture)
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
        shareUri=share2.shareUri,
        groups=[group.name],
    )

    print('Response from getShareObject: ', response)

    # When deleting the share object
    DeleteShareObjectQuery = """
        mutation DeleteShareObject($shareUri: String!){
          deleteShareObject(shareUri:$shareUri)
        }
    """
    response = client.query(
        DeleteShareObjectQuery,
        username=user.userName,
        groups=[group.name],
        shareUri=share2.shareUri,
    )
    assert 'UnauthorizedOperation' in response.errors[0].message

@pytest.mark.dependency(depends=["test_delete_share_object_remaining_items_error"])
def test_revoke_share_item(
        share2,
        share_item2_shared,
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
        shareUri=share2.shareUri,
        groups=[group.name],
    )

    print('Response from getShareObject: ', response)

    assert (
        response.data.getShareObject.status
        == dataall.api.constants.ShareObjectStatus.Draft.value
    )

    # When
    q = """
        mutation revokeSharedItem($shareItemUri: String!) {
          revokeSharedItem(shareItemUri: $shareItemUri)
        }
    """
    response = client.query(
        q,
        username=user.userName,
        shareItemUri=share_item2_shared.shareItemUri,
        groups=[group.name],
    )
    print('Response from revokeSharedItem: ', response)
    assert response.data.revokeSharedItem



def _successfull_processing_for_approved_share_object(db, share):
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

