from .client import *
from dataall.db import models
from dataall.api import constants


@pytest.fixture(scope='module', autouse=True)
def patch_request(module_mocker):
    """we will mock requests.post so no call to cdk proxy will be made"""
    module_mocker.patch('requests.post', return_value=True)


@pytest.fixture(scope='module', autouse=True)
def patch_check_env(module_mocker):
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.check_environment',
        return_value='CDKROLENAME',
    )
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.get_pivot_role_as_part_of_environment', return_value=False
    )


@pytest.fixture(scope='module', autouse=True)
def patch_check_dataset(module_mocker):
    module_mocker.patch(
        'dataall.api.Objects.Dataset.resolvers.check_dataset_account', return_value=True
    )


@pytest.fixture(scope='module', autouse=True)
def patch_es(module_mocker):
    module_mocker.patch('dataall.searchproxy.connect', return_value={})
    module_mocker.patch('dataall.searchproxy.search', return_value={})
    module_mocker.patch('dataall.searchproxy.upsert', return_value={})
    module_mocker.patch('dataall.searchproxy.indexers.upsert_dataset_tables', return_value={})
    module_mocker.patch('dataall.searchproxy.indexers.upsert_dataset', return_value={})
    module_mocker.patch('dataall.searchproxy.indexers.upsert_table', return_value={})
    module_mocker.patch('dataall.searchproxy.indexers.upsert_folder', return_value={})
    module_mocker.patch('dataall.searchproxy.indexers.upsert_dashboard', return_value={})
    module_mocker.patch('dataall.searchproxy.indexers.delete_doc', return_value={})


@pytest.fixture(scope='module', autouse=True)
def patch_stack_tasks(module_mocker):
    module_mocker.patch(
        'dataall.aws.handlers.ecs.Ecs.is_task_running',
        return_value=False,
    )
    module_mocker.patch(
        'dataall.aws.handlers.ecs.Ecs.run_cdkproxy_task',
        return_value='arn:aws:eu-west-1:xxxxxxxx:ecs:task/1222222222',
    )
    module_mocker.patch(
        'dataall.aws.handlers.cloudformation.CloudFormation.describe_stack_resources',
        return_value=True,
    )


@pytest.fixture(scope='module', autouse=True)
def permissions(db):
    with db.scoped_session() as session:
        yield dataall.db.api.Permission.init_permissions(session)


@pytest.fixture(scope='module', autouse=True)
def user(db):
    with db.scoped_session() as session:
        user = dataall.db.models.User(userId='alice@test.com', userName='alice')
        session.add(user)
        yield user


@pytest.fixture(scope='module')
def group(db, user):
    with db.scoped_session() as session:
        group = dataall.db.models.Group(name='testadmins', label='testadmins', owner='alice')
        session.add(group)
        session.commit()
        member = dataall.db.models.GroupMember(
            userName=user.userName,
            groupUri=group.groupUri,
        )
        session.add(member)
        session.commit()
        yield group


@pytest.fixture(scope='module', autouse=True)
def user2(db):
    with db.scoped_session() as session:
        user = dataall.db.models.User(userId='bob@test.com', userName='bob')
        session.add(user)
        yield user


@pytest.fixture(scope='module')
def group2(db, user2):
    with db.scoped_session() as session:
        group = dataall.db.models.Group(name='dataengineers', label='dataengineers', owner=user2.userName)
        session.add(group)
        session.commit()
        member = dataall.db.models.GroupMember(
            userName=user2.userName,
            groupUri=group.groupUri,
        )
        session.add(member)
        session.commit()
        yield group


@pytest.fixture(scope='module', autouse=True)
def user3(db):
    with db.scoped_session() as session:
        user = dataall.db.models.User(userId='david@test.com', userName='david')
        session.add(user)
        yield user


@pytest.fixture(scope='module')
def group3(db, user3):
    with db.scoped_session() as session:
        group = dataall.db.models.Group(name='datascientists', label='datascientists', owner=user3.userName)
        session.add(group)
        session.commit()
        member = dataall.db.models.GroupMember(
            userName=user3.userName,
            groupUri=group.groupUri,
        )
        session.add(member)
        session.commit()
        yield group


@pytest.fixture(scope='module')
def group4(db, user3):
    with db.scoped_session() as session:
        group = dataall.db.models.Group(name='externals', label='externals', owner=user3.userName)
        session.add(group)
        session.commit()
        member = dataall.db.models.GroupMember(
            userName=user3.userName,
            groupUri=group.groupUri,
        )
        session.add(member)
        session.commit()
        yield group


@pytest.fixture(scope='module')
def tenant(db, group, group2, permissions, user, user2, user3, group3, group4):
    with db.scoped_session() as session:
        tenant = dataall.db.api.Tenant.save_tenant(session, name='dataall', description='Tenant dataall')
        dataall.db.api.TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group.name,
            permissions=dataall.db.permissions.TENANT_ALL,
            tenant_name='dataall',
        )
        dataall.db.api.TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group2.name,
            permissions=dataall.db.permissions.TENANT_ALL,
            tenant_name='dataall',
        )
        dataall.db.api.TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group3.name,
            permissions=dataall.db.permissions.TENANT_ALL,
            tenant_name='dataall',
        )
        dataall.db.api.TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group4.name,
            permissions=dataall.db.permissions.TENANT_ALL,
            tenant_name='dataall',
        )
        yield tenant


@pytest.fixture(scope='module', autouse=True)
def dataset(client, patch_es):
    cache = {}

    def factory(
        org: models.Organization,
        env: models.Environment,
        name: str,
        owner: str,
        group: str,
    ) -> models.Dataset:
        key = f'{org.organizationUri}-{env.environmentUri}-{name}-{group}'
        if cache.get(key):
            print('found in cache ', cache[key])
            return cache.get(key)
        response = client.query(
            """
            mutation CreateDataset($input:NewDatasetInput){
                createDataset(
                input:$input
                ){
                    datasetUri
                    label
                    description
                    AwsAccountId
                    S3BucketName
                    GlueDatabaseName
                    owner
                    region,
                    businessOwnerEmail
                    businessOwnerDelegationEmails
                    SamlAdminGroupName
                    GlueCrawlerName
                    tables{
                     nodes{
                      tableUri
                     }
                    }
                    locations{
                     nodes{
                      locationUri
                     }
                    }
                    stack{
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
                    topics
                    language
                    confidentiality
                    organization{
                        organizationUri
                        label
                    }
                    shares{
                        nodes{
                         shareUri
                        }
                    }
                    terms{
                        count
                        nodes{
                            __typename
                            ...on Term {
                                nodeUri
                                path
                                label
                            }
                        }
                    }
                    environment{
                        environmentUri
                        label
                        region
                        subscriptionsEnabled
                        subscriptionsProducersTopicImported
                        subscriptionsConsumersTopicImported
                        subscriptionsConsumersTopicName
                        subscriptionsProducersTopicName
                        organization{
                            organizationUri
                            label
                        }
                    }
                    statistics{
                        tables
                        locations
                        upvotes
                    }
                }
            }
            """,
            username=owner,
            groups=[group],
            input={
                'owner': owner,
                'label': f'{name}',
                'description': 'test dataset {name}',
                'businessOwnerEmail': 'jeff@amazon.com',
                'tags': random_tags(),
                'businessOwnerDelegationEmails': random_emails(),
                'environmentUri': env.environmentUri,
                'SamlAdminGroupName': group or random_group(),
                'organizationUri': org.organizationUri,
            },
        )
        print('==>', response)
        return response.data.createDataset

    yield factory


@pytest.fixture(scope='module', autouse=True)
def env(client):
    cache = {}

    def factory(org, envname, owner, group, account, region, desc='test'):
        key = f"{org.organizationUri}{envname}{owner}{''.join(group or '-')}{account}{region}"
        if cache.get(key):
            return cache[key]
        response = client.query(
            """mutation CreateEnv($input:NewEnvironmentInput){
                createEnvironment(input:$input){
                    organization{
                        organizationUri
                    }
                    environmentUri
                    label
                    AwsAccountId
                    SamlGroupName
                    region
                    name
                    owner
                }
            }""",
            username=f'{owner}',
            groups=[group],
            input={
                'label': f'{envname}',
                'description': f'{desc}',
                'organizationUri': org.organizationUri,
                'AwsAccountId': account,
                'tags': ['a', 'b', 'c'],
                'region': f'{region}',
                'SamlGroupName': f'{group}',
                'dashboardsEnabled': True,
                'vpcId': 'vpc-123456',
            },
        )
        cache[key] = response.data.createEnvironment
        return cache[key]

    yield factory


@pytest.fixture(scope="module")
def environment(db):
    def factory(
        organization: models.Organization,
        awsAccountId: str,
        label: str,
        owner: str,
        samlGroupName: str,
        environmentDefaultIAMRoleName: str,
        dashboardsEnabled: bool = False,
    ) -> models.Environment:
        with db.scoped_session() as session:
            env = models.Environment(
                organizationUri=organization.organizationUri,
                AwsAccountId=awsAccountId,
                region="eu-central-1",
                label=label,
                owner=owner,
                tags=[],
                description="desc",
                SamlGroupName=samlGroupName,
                EnvironmentDefaultIAMRoleName=environmentDefaultIAMRoleName,
                EnvironmentDefaultIAMRoleArn=f"arn:aws:iam::{awsAccountId}:role/{environmentDefaultIAMRoleName}",
                CDKRoleArn=f"arn:aws::{awsAccountId}:role/EnvRole",
                dashboardsEnabled=dashboardsEnabled,
            )
            session.add(env)
            session.commit()
        return env

    yield factory

@pytest.fixture(scope="module")
def dataset_model(db):
    def factory(
        organization: models.Organization,
        environment: models.Environment,
        label: str,
    ) -> models.Dataset:
        with db.scoped_session() as session:
            dataset = models.Dataset(
                organizationUri=organization.organizationUri,
                environmentUri=environment.environmentUri,
                label=label,
                owner=environment.owner,
                stewards=environment.SamlGroupName,
                SamlAdminGroupName=environment.SamlGroupName,
                businessOwnerDelegationEmails=["foo@amazon.com"],
                name=label,
                S3BucketName=label,
                GlueDatabaseName="gluedatabase",
                KmsAlias="kmsalias",
                AwsAccountId=environment.AwsAccountId,
                region=environment.region,
                IAMDatasetAdminUserArn=f"arn:aws:iam::{environment.AwsAccountId}:user/dataset",
                IAMDatasetAdminRoleArn=f"arn:aws:iam::{environment.AwsAccountId}:role/dataset",
            )
            session.add(dataset)
            session.commit()
            return dataset

    yield factory


@pytest.fixture(scope="module")
def environment_group(db):
    def factory(
        environment: models.Environment,
        group: models.Group,
    ) -> models.EnvironmentGroup:
        with db.scoped_session() as session:

            env_group = models.EnvironmentGroup(
                environmentUri=environment.environmentUri,
                groupUri=group.name,
                environmentIAMRoleArn=environment.EnvironmentDefaultIAMRoleArn,
                environmentIAMRoleName=environment.EnvironmentDefaultIAMRoleName,
                environmentAthenaWorkGroup="workgroup",
            )
            session.add(env_group)
            dataall.db.api.ResourcePolicy.attach_resource_policy(
                session=session,
                resource_uri=environment.environmentUri,
                group=group.name,
                permissions=dataall.db.permissions.ENVIRONMENT_ALL,
                resource_type=dataall.db.models.Environment.__name__,
            )
            session.commit()
            return env_group

    yield factory


@pytest.fixture(scope="module")
def share(db):
    def factory(
            dataset: models.Dataset,
            environment: models.Environment,
            env_group: models.EnvironmentGroup,
            owner: str,
            status: str
    ) -> models.ShareObject:
        with db.scoped_session() as session:
            share = models.ShareObject(
                datasetUri=dataset.datasetUri,
                environmentUri=environment.environmentUri,
                owner=owner,
                groupUri=env_group.groupUri,
                principalId=env_group.groupUri,
                principalType=constants.PrincipalType.Group.value,
                principalIAMRoleName=env_group.environmentIAMRoleName,
                status=status,
            )
            session.add(share)
            session.commit()
            dataall.db.api.ResourcePolicy.attach_resource_policy(
                session=session,
                group=env_group.groupUri,
                permissions=dataall.db.permissions.SHARE_OBJECT_REQUESTER,
                resource_uri=share.shareUri,
                resource_type=models.ShareObject.__name__,
            )
            dataall.db.api.ResourcePolicy.attach_resource_policy(
                session=session,
                group=dataset.SamlAdminGroupName,
                permissions=dataall.db.permissions.SHARE_OBJECT_REQUESTER,
                resource_uri=share.shareUri,
                resource_type=dataall.db.models.ShareObject.__name__,
            )
            dataall.db.api.ResourcePolicy.attach_resource_policy(
                session=session,
                group=dataset.stewards,
                permissions=dataall.db.permissions.SHARE_OBJECT_APPROVER,
                resource_uri=share.shareUri,
                resource_type=dataall.db.models.ShareObject.__name__,
            )
            if dataset.SamlAdminGroupName != environment.SamlGroupName:
                dataall.db.api.ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=environment.SamlGroupName,
                    permissions=dataall.db.permissions.SHARE_OBJECT_REQUESTER,
                    resource_uri=share.shareUri,
                    resource_type=dataall.db.models.ShareObject.__name__,
                )
            session.commit()
            return share

    yield factory


@pytest.fixture(scope="module")
def share_item(db):
    def factory(
            share: models.ShareObject,
            table: models.DatasetTable,
            status: str
    ) -> models.ShareObjectItem:
        with db.scoped_session() as session:
            share_item = models.ShareObjectItem(
                shareUri=share.shareUri,
                owner="alice",
                itemUri=table.tableUri,
                itemType=constants.ShareableType.Table.value,
                itemName=table.name,
                status=status,
            )
            session.add(share_item)
            session.commit()
            return share_item

    yield factory


@pytest.fixture(scope='module', autouse=True)
def location(db):
    cache = {}

    def factory(dataset: models.Dataset, name, username) -> models.DatasetStorageLocation:
        key = f'{dataset.datasetUri}-{name}'
        if cache.get(key):
            return cache.get(key)
        with db.scoped_session() as session:
            ds_location = models.DatasetStorageLocation(
                name=name,
                label=name,
                owner=username,
                datasetUri=dataset.datasetUri,
                S3BucketName=dataset.S3BucketName,
                region=dataset.region,
                AWSAccountId=dataset.AwsAccountId,
                S3Prefix=f'{name}',
            )
            session.add(ds_location)
        return ds_location

    yield factory


@pytest.fixture(scope='module', autouse=True)
def table(db):
    cache = {}

    def factory(dataset: models.Dataset, name, username) -> models.DatasetTable:
        key = f'{dataset.datasetUri}-{name}'
        if cache.get(key):
            return cache.get(key)
        with db.scoped_session() as session:
            table = models.DatasetTable(
                name=name,
                label=name,
                owner=username,
                datasetUri=dataset.datasetUri,
                GlueDatabaseName=dataset.GlueDatabaseName,
                GlueTableName=name,
                region=dataset.region,
                AWSAccountId=dataset.AwsAccountId,
                S3BucketName=dataset.S3BucketName,
                S3Prefix=f'{name}',
            )
            session.add(table)
        return table

    yield factory


@pytest.fixture(scope='module', autouse=True)
def org(client):
    cache = {}

    def factory(orgname, owner, group):
        key = orgname + owner + group
        if cache.get(key):
            print(f'returning item from cached key {key}')
            return cache.get(key)
        response = client.query(
            """mutation CreateOrganization($input:NewOrganizationInput){
                createOrganization(input:$input){
                    organizationUri
                    label
                    name
                    owner
                    SamlGroupName
                }
            }""",
            username=f'{owner}',
            groups=[group],
            input={
                'label': f'{orgname}',
                'description': f'test',
                'tags': ['a', 'b', 'c'],
                'SamlGroupName': f'{group}',
            },
        )
        cache[key] = response.data.createOrganization
        return cache[key]

    yield factory


@pytest.fixture(scope='module')
def org_fixture(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module')
def env_fixture(env, org_fixture, user, group, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch('dataall.api.Objects.Environment.resolvers.check_environment', return_value=True)
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.get_pivot_role_as_part_of_environment', return_value=False
    )
    env1 = env(org_fixture, 'dev', 'alice', 'testadmins', '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module')
def dataset_fixture(env_fixture, org_fixture, dataset, group, module_mocker) -> dataall.db.models.Dataset:
    module_mocker.patch(
        'dataall.api.Objects.Dataset.resolvers.check_dataset_account', return_value=True
    )
    yield dataset(
        org=org_fixture,
        env=env_fixture,
        name='dataset1',
        owner=env_fixture.owner,
        group=group.name,
    )


@pytest.fixture(scope='module')
def cluster(env_fixture, org_fixture, client, group):
    ouri = org_fixture.organizationUri
    euri = env_fixture.environmentUri
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


@pytest.fixture(scope='module')
def sgm_notebook(client, tenant, group, env_fixture) -> dataall.db.models.SagemakerNotebook:
    response = client.query(
        """
        mutation createSagemakerNotebook($input:NewSagemakerNotebookInput){
            createSagemakerNotebook(input:$input){
                notebookUri
                label
                description
                tags
                owner
                userRoleForNotebook
                SamlAdminGroupName
                VpcId
                SubnetId
                VolumeSizeInGB
                InstanceType
            }
        }
        """,
        input={
            'label': 'my pipeline',
            'SamlAdminGroupName': group.name,
            'tags': [group.name],
            'environmentUri': env_fixture.environmentUri,
            'VpcId': 'vpc-123567',
            'SubnetId': 'subnet-123567',
            'VolumeSizeInGB': 32,
            'InstanceType': 'ml.m5.xlarge',
        },
        username='alice',
        groups=[group.name],
    )
    yield response.data.createSagemakerNotebook


@pytest.fixture(scope='module')
def pipeline(client, tenant, group, env_fixture) -> models.DataPipeline:
    response = client.query(
        """
        mutation createDataPipeline ($input:NewDataPipelineInput){
            createDataPipeline(input:$input){
                DataPipelineUri
                label
                description
                tags
                owner
                repo
                userRoleForPipeline
            }
        }
        """,
        input={
            'label': 'my pipeline',
            'SamlGroupName': group.name,
            'tags': [group.name],
            'environmentUri': env_fixture.environmentUri,
            'devStrategy': 'trunk',
        },
        username='alice',
        groups=[group.name],
    )
    yield response.data.createDataPipeline


@pytest.fixture(scope='module')
def sgm_studio(client, tenant, group, env_fixture, module_mocker) -> models.SagemakerStudioUserProfile:
    module_mocker.patch(
        'dataall.aws.handlers.sagemaker_studio.SagemakerStudio.get_sagemaker_studio_domain',
        return_value={'DomainId': 'test'},
    )
    response = client.query(
        """
            mutation createSagemakerStudioUserProfile($input:NewSagemakerStudioUserProfileInput){
            createSagemakerStudioUserProfile(input:$input){
                sagemakerStudioUserProfileUri
                name
                label
                created
                description
                SamlAdminGroupName
                environmentUri
                tags
            }
        }
            """,
        input={
            'label': f'test1',
            'SamlAdminGroupName': group.name,
            'environmentUri': env_fixture.environmentUri,
        },
        username='alice',
        groups=[group.name],
    )
    yield response.data.createSagemakerStudioUserProfile
