import typing


import pytest
import dataall
from dataall.api.constants import RedshiftClusterRole


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
def table1(table, dataset1):
    yield table(dataset1, name='table1', username=dataset1.owner)


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
def table2(table, dataset2):
    yield table(dataset2, name='table2', username=dataset2.owner)


@pytest.fixture(scope='module', autouse=True)
def share(
    client, dataset1, env2, db, user2, group2, env1, user, group, dataset2, table2
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
        groups=[group.name],
        datasetUri=dataset2.datasetUri,
        input={
            'environmentUri': env1.environmentUri,
            'groupUri': group.name,
            'principalId': group.name,
            'principalType': dataall.api.constants.PrincipalType.Group.name,
        },
    )
    print(response)

    assert response.data.createShareObject.dataset.datasetUri == dataset2.datasetUri
    assert (
        response.data.createShareObject.status
        == dataall.api.constants.ShareObjectStatus.Draft.name
    )
    assert response.data.createShareObject.owner == user.userName
    query = """
        mutation AddSharedItem($shareUri:String!,$input:AddSharedItemInput){
            addSharedItem(shareUri:$shareUri,input:$input){
                shareUri
                shareItemUri
                itemUri
            }
        }
        """
    shareUri = response.data.createShareObject.shareUri
    response = client.query(
        query,
        username=user.userName,
        shareUri=shareUri,
        groups=[group.name],
        input={
            'itemUri': table2.tableUri,
            'itemType': dataall.api.constants.ShareableType.Table.name,
        },
    )
    query = """
            mutation submitShareObject($shareUri:String!){
                submitShareObject(shareUri:$shareUri){
                    status
                    owner
                }
            }
            """

    response = client.query(
        query, username=user.userName, shareUri=shareUri, groups=[group.name]
    )
    assert response.data.submitShareObject.status == 'PendingApproval'

    query = """
                mutation approveShareObject($shareUri:String!,$filter:ShareableObjectFilter){
                    approveShareObject(shareUri:$shareUri){
                        status
                        owner
                        items(filter:$filter){
                            count
                            page
                            pages
                            hasNext
                            hasPrevious
                            nodes{
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
        shareUri=shareUri,
        groups=[group2.name],
    )
    assert response.data.approveShareObject.status == 'Approved'


@pytest.fixture(scope='module')
def cluster(env1, org1, client, module_mocker, group):
    module_mocker.patch('requests.post', return_value=True)
    ouri = org1.organizationUri
    euri = env1.environmentUri
    group_name = group.name
    res = client.query(
        """
    mutation createRedshiftCluster {
        createRedshiftCluster(
            environmentUri:"%(euri)s",
            clusterInput:{
                label : "mycluster",
                description:"a test cluster",
                vpc: "vpc-12345",
                databaseName: "mydb",
                masterDatabaseName: "masterDatabaseName",
                masterUsername:"masterUsername",
                nodeType: "multi-node",
                numberOfNodes: 2,
                subnetIds: ["subnet-1","subnet-2"],
                securityGroupIds: ["sg-1","sg-2"],
                tags:["test"],
                SamlGroupName: "%(group_name)s"
            }
        ){
            clusterUri
            label
            description
            tags
            databaseName
            masterDatabaseName
            masterUsername
            nodeType
            numberOfNodes
            subnetIds
            securityGroupIds
            userRoleForCluster
            userRoleInEnvironment
            owner

        }
        }
    """
        % vars(),
        'alice',
        groups=[group_name],
    )
    print(res)
    yield res.data.createRedshiftCluster


def test_create(cluster):
    assert cluster.clusterUri is not None
    assert cluster.label == 'mycluster'
    assert cluster.description == 'a test cluster'
    assert cluster.tags[0] == 'test'
    assert cluster.databaseName == 'mydb'
    assert cluster.masterDatabaseName == 'masterDatabaseName'
    assert cluster.masterUsername == 'masterUsername'
    assert cluster.nodeType == 'multi-node'
    assert cluster.numberOfNodes == 2
    assert cluster.subnetIds[0] == 'subnet-1'
    assert cluster.securityGroupIds[0] == 'sg-1'
    assert cluster.userRoleForCluster == RedshiftClusterRole.Creator.name


def test_get_cluster_as_owner(cluster, client, group):
    duri = cluster.clusterUri
    res = client.query(
        """
        query getRedshiftCluster{
        getRedshiftCluster(clusterUri:"%(duri)s"){
            clusterUri
            owner
            label
            description
            tags
            masterDatabaseName
            masterUsername
            nodeType
            numberOfNodes
            subnetIds
            securityGroupIds
            userRoleForCluster
            userRoleInEnvironment
        }
        }
    """
        % vars(),
        username='alice',
        groups=[group.name],
    )
    print(res)
    assert res.data.getRedshiftCluster.clusterUri == duri


def test_get_cluster_anonymous(cluster, client):
    print(' [¨] ' * 10)
    duri = cluster.clusterUri
    res = client.query(
        """
        query getRedshiftCluster{
        getRedshiftCluster(clusterUri:"%(duri)s"){
            clusterUri
            label
            description
            tags
            masterDatabaseName
            masterUsername
            nodeType
            numberOfNodes
            subnetIds
            securityGroupIds
            userRoleForCluster
            userRoleInEnvironment
        }
        }
    """
        % vars(),
        username='bob',
    )
    print(res)
    assert not res.data.getRedshiftCluster


def test_list_env_clusters_no_filter(env1, cluster, client, group):
    euri = env1.environmentUri
    res = client.query(
        """
        query listEnvironmentClusters{
        listEnvironmentClusters(environmentUri:"%(euri)s"){
                count
                nodes{
                    clusterUri
                    label
                    userRoleForCluster
                }
            }
            }
    """
        % vars(),
        username='alice',
        groups=[group.name],
    )
    print(res)
    assert res.data.listEnvironmentClusters.count == 1


def test_list_env_clusters_filter_term(env1, cluster, client, group):
    euri = env1.environmentUri
    res = client.query(
        """
            query listEnvironmentClusters{
            listEnvironmentClusters(environmentUri:"%(euri)s",
             filter:{
                 term : "mycluster"
             }
         ){
             count
             nodes{
                 clusterUri
                 label
                 userRoleForCluster
             }
         }
         }
         """
        % vars(),
        username='alice',
        groups=[group.name],
    )
    assert res.data.listEnvironmentClusters.count == 1


def test_list_cluster_available_datasets(env1, cluster, dataset1, client, group):
    res = client.query(
        """
        query ListRedshiftClusterAvailableDatasets($clusterUri:String!,$filter:RedshiftClusterDatasetFilter){
                listRedshiftClusterAvailableDatasets(clusterUri:$clusterUri,filter:$filter){
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    nodes{
                        datasetUri
                        name
                        label
                        region
                        tags
                        userRoleForDataset
                        redshiftClusterPermission(clusterUri:$clusterUri)
                        description
                        organization{
                            name
                            organizationUri
                            label
                        }
                        statistics{
                            tables
                            locations
                        }
                        environment{
                            environmentUri
                            name
                            AwsAccountId
                            SamlGroupName
                            region
                        }

                    }
                }
            }""",
        clusterUri=cluster.clusterUri,
        username='alice',
        groups=[group.name],
    )
    print(res)
    assert res.data.listRedshiftClusterAvailableDatasets.count == 2


def test_add_dataset_to_cluster(env1, cluster, dataset1, client, db, group):
    with db.scoped_session() as session:
        cluster = session.query(dataall.db.models.RedshiftCluster).get(
            cluster.clusterUri
        )
        cluster.status = 'available'
        session.commit()
    res = client.query(
        """
        mutation addDatasetToRedshiftCluster(
            $clusterUri:String,
            $datasetUri:String,
        ){
            addDatasetToRedshiftCluster(
                clusterUri:$clusterUri,
                datasetUri:$datasetUri
            )
        }
        """,
        clusterUri=cluster.clusterUri,
        datasetUri=dataset1.datasetUri,
        username='alice',
        groups=[group.name],
    )
    print(res)


def test_cluster_tables_copy(env1, cluster, dataset1, env2, client, db, group):
    res = client.query(
        """
        query listRedshiftClusterAvailableDatasetTables($clusterUri:String!,$filter:DatasetTableFilter){
                listRedshiftClusterAvailableDatasetTables(clusterUri:$clusterUri,filter:$filter){
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    count
                    nodes{
                        tableUri
                        name
                        label
                        GlueDatabaseName
                        GlueTableName
                        S3Prefix
                    }
                }
            }""",
        clusterUri=cluster.clusterUri,
        username='alice',
        groups=[group.name],
    )
    print(res)
    assert res.data.listRedshiftClusterAvailableDatasetTables.count == 2

    table = res.data.listRedshiftClusterAvailableDatasetTables.nodes[0]

    res = client.query(
        """
        mutation enableRedshiftClusterDatasetTableCopy(
            $clusterUri:String!,
            $datasetUri:String!,
            $tableUri:String!,
            $schema: String!,
            $dataLocation: String!
        ){
            enableRedshiftClusterDatasetTableCopy(
                clusterUri:$clusterUri,
                datasetUri:$datasetUri,
                tableUri:$tableUri,
                schema:$schema,
                dataLocation:$dataLocation
            )
        }
        """,
        clusterUri=cluster.clusterUri,
        datasetUri=dataset1.datasetUri,
        tableUri=table.tableUri,
        schema='myschema',
        username='alice',
        groups=[group.name],
        dataLocation='yes',
    )
    print(res)
    assert res.data.enableRedshiftClusterDatasetTableCopy

    res = client.query(
        """
        query listRedshiftClusterCopyEnabledTables($clusterUri:String!,$filter:DatasetTableFilter){
                listRedshiftClusterCopyEnabledTables(clusterUri:$clusterUri,filter:$filter){
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        count
                        nodes{
                            tableUri
                            name
                            label
                            GlueDatabaseName
                            GlueTableName
                            S3Prefix
                            RedshiftSchema(clusterUri:$clusterUri)
                            RedshiftCopyDataLocation(clusterUri:$clusterUri)
                        }
                }
            }""",
        clusterUri=cluster.clusterUri,
        username='alice',
        groups=[group.name],
    )
    print(res)
    assert res.data.listRedshiftClusterCopyEnabledTables.count == 1

    res = client.query(
        """
        mutation disableRedshiftClusterDatasetTableCopy(
            $clusterUri:String!,
            $datasetUri:String!,
            $tableUri:String!
        ){
            disableRedshiftClusterDatasetTableCopy(
                clusterUri:$clusterUri,
                datasetUri:$datasetUri,
                tableUri:$tableUri
            )
        }
        """,
        clusterUri=cluster.clusterUri,
        datasetUri=dataset1.datasetUri,
        tableUri=table.tableUri,
        username='alice',
        groups=[group.name],
    )
    print(res)
    assert res.data.disableRedshiftClusterDatasetTableCopy

    res = client.query(
        """
        query listRedshiftClusterCopyEnabledTables($clusterUri:String!,$filter:DatasetTableFilter){
                listRedshiftClusterCopyEnabledTables(clusterUri:$clusterUri,filter:$filter){
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        count
                        nodes{
                            tableUri
                            name
                            label
                            GlueDatabaseName
                            GlueTableName
                            S3Prefix
                        }
                }
            }""",
        clusterUri=cluster.clusterUri,
        username='alice',
        groups=[group.name],
    )
    print(res)
    assert res.data.listRedshiftClusterCopyEnabledTables.count == 0


def test_delete_cluster(client, cluster, env1, org1, db, module_mocker, group, user):
    module_mocker.patch(
        'dataall.aws.handlers.service_handlers.Worker.queue', return_value=True
    )
    response = client.query(
        """
        mutation deleteRedshiftCluster($clusterUri:String!,$deleteFromAWS:Boolean){
            deleteRedshiftCluster(clusterUri:$clusterUri, deleteFromAWS:$deleteFromAWS)
        }
        """,
        clusterUri=cluster.clusterUri,
        deleteFromAWS=True,
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.deleteRedshiftCluster
