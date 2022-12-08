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


def test_init(tables1, tables2):
    assert True


def test_request_access_unauthorized(client, dataset1, env2, group2, group3):
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


def test_request_access_authorized(client, dataset1, env2, db, user2, group2, env1):
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

    assert response.data.createShareObject.shareUri


def test_get_share_object(client, share1, user, env1group):
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
    assert response.data.getShareObject.principal.principalType == dataall.api.constants.PrincipalType.Group.name
    assert response.data.getShareObject.principal.principalIAMRoleName
    assert response.data.getShareObject.principal.SamlGroupName
    assert response.data.getShareObject.principal.region


def test_list_dataset_share_objects(
        client, dataset1, env1, user, user3, env2, db, user2, group2, group, group4
):
    q = """
    query GetDataset(
        $datasetUri:String!,
    ){
        getDataset(datasetUri:$datasetUri){
            datasetUri
            shares{
                count
                nodes{
                    shareUri
                    status
                    userRoleForShareObject
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


def test_add_item(
        dataset1,
        env1,
        client,
        user2,
        group2,
        env2,
        org2,
        user,
        group3,
        user3,
        module_mocker,
        group,
):
    module_mocker.patch(
        'dataall.api.Objects.Stack.stack_helper.deploy_stack',
        return_value=True,
    )
    get_share_object_query = q = """
    query GetDataset(
        $datasetUri:String!,
    ){
        getDataset(datasetUri:$datasetUri){
            datasetUri
            tables{
                count
                nodes{
                    tableUri

                }

            }
            shares{
                count
                nodes{
                    owner
                    shareUri
                    status

                }
            }
        }
    }
    """
    response = client.query(
        get_share_object_query,
        username=dataset1.owner,
        groups=[group.name],
        datasetUri=dataset1.datasetUri,
    )
    share_object = response.data.getDataset.shares.nodes[0]
    this_dataset_tables = response.data.getDataset.tables.nodes
    print(this_dataset_tables)
    query = """
    mutation AddSharedItem($shareUri:String!,$input:AddSharedItemInput){
        addSharedItem(shareUri:$shareUri,input:$input){
            shareUri
            shareItemUri
            itemUri
        }
    }
    """

    response = client.query(
        query,
        username=dataset1.owner,
        shareUri=share_object.shareUri,
        input={
            'itemUri': 'foo',
            'itemType': dataall.api.constants.ShareableType.Table.name,
        },
        groups=[group.name],
    )

    assert 'ResourceNotFound' in response.errors[0].message

    response = client.query(
        query,
        username='noneofmybusiness',
        groups=['anonymous'],
        shareUri=share_object.shareUri,
        input={
            'itemUri': 'foo',
            'itemType': dataall.api.constants.ShareableType.Table.name,
        },
    )
    assert 'UnauthorizedOperation' in response.errors[0].message

    response = client.query(
        query,
        username=share_object.owner,
        groups=[group2.name],
        shareUri=share_object.shareUri,
        input={
            'itemUri': 'foo',
            'itemType': dataall.api.constants.ShareableType.Table.name,
        },
    )

    assert 'ResourceNotFound' in response.errors[0].message

    random_table: dataall.db.models.DatasetTable = random.choice(this_dataset_tables)
    response = client.query(
        query,
        username=share_object.owner,
        groups=[group2.name],
        shareUri=share_object.shareUri,
        input={
            'itemUri': random_table.tableUri,
            'itemType': dataall.api.constants.ShareableType.Table.name,
        },
    )

    assert response.data.addSharedItem.shareUri == share_object.shareUri
    share_item_uri = response.data.addSharedItem.shareItemUri

    query = """
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
        query,
        username=user2.userName,
        shareUri=share_object.shareUri,
        groups=[group2.name],
    )

    assert (
            response.data.getShareObject.status
            == dataall.api.constants.ShareObjectStatus.Draft.name
    )
    assert (
            response.data.getShareObject.principal.principalId
            == group2.name
    )
    assert (
            response.data.getShareObject.principal.principalType
            == dataall.api.constants.PrincipalType.Group.name
    )
    assert response.data.getShareObject.dataset.datasetUri == dataset1.datasetUri

    query = """
        mutation submitShareObject($shareUri:String!){
            submitShareObject(shareUri:$shareUri){
                status
                owner
                userRoleForShareObject
            }
        }
        """

    response = client.query(
        query,
        username=user2.userName,
        shareUri=share_object.shareUri,
        groups=[group2.name],
    )
    assert response.data.submitShareObject.status == 'PendingApproval'
    assert response.data.submitShareObject.userRoleForShareObject == 'Requesters'

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
        username=user3.userName,
        shareUri=share_object.shareUri,
        groups=[group3.name],
    )
    assert response.data.approveShareObject.status == 'Approved'
    assert response.data.approveShareObject.userRoleForShareObject == 'Approvers'

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

    query = """
                mutation rejectShareObject($shareUri:String!){
                    rejectShareObject(shareUri:$shareUri){
                        status
                        owner
                    }
                }
                """

    response = client.query(
        query,
        username=user3.userName,
        shareUri=share_object.shareUri,
        groups=[group3.name],
    )
    assert response.data.rejectShareObject.status == 'Rejected'
    query = """
        mutation RemoveSharedItem($shareItemUri:String!){
            removeSharedItem(shareItemUri:$shareItemUri)
        }
        """
    response = client.query(
        query,
        username=share_object.owner,
        groups=[group2.name],
        shareItemUri=share_item_uri,
    )

    assert response.data.removeSharedItem
    received_requests = """
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
        received_requests, username=user.userName, groups=[group.name]
    )
    assert response.data.getShareRequestsToMe.count == 0
    received_requests = """
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
        received_requests, username=user3.userName, groups=[group3.name]
    )
    assert response.data.getShareRequestsToMe.count == 1

    sent_requests = """
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
        sent_requests, username=user2.userName, groups=[group2.name]
    )
    assert response.data.getShareRequestsFromMe.count == 1

    sent_requests = """
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
        sent_requests, username=user3.userName, groups=[group3.name]
    )
    assert response.data.getShareRequestsFromMe.count == 0


def test_notifications(client, db, user):
    list = """
                query ListNotifications{
                    listNotifications{
                        count
                        nodes{
                            notificationUri
                            message
                            type
                            is_read
                        }
                    }
                }
                """
    response = client.query(list, username=user.userName)
    assert (
            response.data.listNotifications.nodes[0].type
            == dataall.db.models.NotificationType.SHARE_OBJECT_SUBMITTED.name
    )
    notificationUri = response.data.listNotifications.nodes[0].notificationUri
    query = """
                query CountUnread{
                    countUnreadNotifications
                }
                """
    response = client.query(query, username=user.userName)
    assert response.data.countUnreadNotifications == 3
    read = """
            mutation markAsRead($notificationUri:String!){
                markNotificationAsRead(notificationUri:$notificationUri)
            }
            """
    response = client.query(
        read, username=user.userName, notificationUri=notificationUri
    )
    assert response

    query = """
                    query countReadNotifications{
                        countReadNotifications
                    }
                    """
    response = client.query(query, username=user.userName)
    assert response.data.countReadNotifications == 1
    read = """
                mutation deleteNotification($notificationUri:String!){
                    deleteNotification(notificationUri:$notificationUri)
                }
                """
    response = client.query(
        read, username=user.userName, notificationUri=notificationUri
    )
    assert response
    query = """
                        query countDeletedNotifications{
                            countDeletedNotifications
                        }
                        """
    response = client.query(query, username=user.userName)
    assert response.data.countDeletedNotifications == 1

    query = """
            query ListNotifications($filter:NotificationFilter){
                    listNotifications(filter:$filter){
                        count
                        nodes{
                            notificationUri
                            message
                            type
                            is_read
                        }
                    }
                }
    """
    response = client.query(query, username=user.userName, filter={'unread': True})
    assert response.data.listNotifications.count == 2

    query = """
                query ListNotifications($filter:NotificationFilter){
                        listNotifications(filter:$filter){
                            count
                            nodes{
                                notificationUri
                                message
                                type
                                is_read
                            }
                        }
                    }
        """
    response = client.query(query, username=user.userName, filter={'read': True})
    assert response.data.listNotifications.count == 0

    query = """
                    query ListNotifications($filter:NotificationFilter){
                            listNotifications(filter:$filter){
                                count
                                nodes{
                                    notificationUri
                                    message
                                    type
                                    is_read
                                }
                            }
                        }
            """
    response = client.query(query, username=user.userName, filter={'archived': True})
    assert response.data.listNotifications.count == 1


def test_delete_share_object(client, dataset1, group, user2, group2, env2):
    get_share_object_query = """
    query GetDataset(
        $datasetUri:String!,
    ){
        getDataset(datasetUri:$datasetUri){
            datasetUri
            tables{
                count
                nodes{
                    tableUri

                }

            }
            shares{
                count
                nodes{
                    owner
                    shareUri
                    status

                }
            }
        }
    }
    """
    response = client.query(
        get_share_object_query,
        username=dataset1.owner,
        groups=[group.name],
        datasetUri=dataset1.datasetUri,
    )
    share_object = response.data.getDataset.shares.nodes[0]

    delete_share_object_query = """
    mutation DeleteShareObject($shareUri: String!){
      deleteShareObject(shareUri:$shareUri)
    }
    """
    response = client.query(
        delete_share_object_query,
        username=dataset1.owner,
        groups=[group.name],
        shareUri=share_object.shareUri,
    )
    assert response.data.deleteShareObject

    create_shared_object_query = """
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

    client.query(
        create_shared_object_query,
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

    add_item_query = """
    mutation AddSharedItem($shareUri:String!,$input:AddSharedItemInput){
        addSharedItem(shareUri:$shareUri,input:$input){
            shareUri
            shareItemUri
            itemUri
        }
    }
    """
    response = client.query(
        get_share_object_query,
        username=dataset1.owner,
        groups=[group.name],
        datasetUri=dataset1.datasetUri,
    )

    share_object = response.data.getDataset.shares.nodes[0]

    this_dataset_tables = response.data.getDataset.tables.nodes
    random_table: dataall.db.models.DatasetTable = random.choice(this_dataset_tables)
    response = client.query(
        add_item_query,
        username=share_object.owner,
        groups=[group2.name],
        shareUri=share_object.shareUri,
        input={
            'itemUri': random_table.tableUri,
            'itemType': dataall.api.constants.ShareableType.Table.name,
        },
    )

    shared_item = response.data.addSharedItem

    response = client.query(
        delete_share_object_query,
        username=user2.userName, groups=[group2.name],
        shareUri=share_object.shareUri,
    )
    assert 'ShareItemsFound' in response.errors[0].message

    remove_item_query = """
        mutation RemoveSharedItem($shareItemUri:String!){
            removeSharedItem(shareItemUri:$shareItemUri)
        }
    """
    client.query(
        remove_item_query,
        username=user2.userName,
        groups=[group2.name],
        shareItemUri=shared_item.shareItemUri
    )

    response = client.query(
        delete_share_object_query,
        username=user2.userName, groups=[group2.name],
        shareUri=share_object.shareUri,
    )
    assert response.data.deleteShareObject
