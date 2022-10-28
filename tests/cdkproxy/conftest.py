import pytest

from dataall.db import models, api


@pytest.fixture(scope='module', autouse=True)
def permissions(db):
    with db.scoped_session() as session:
        yield api.Permission.init_permissions(session)


@pytest.fixture(scope='module', autouse=True)
def org(db) -> models.Organization:
    with db.scoped_session() as session:
        org = models.Organization(
            name='org', owner='me', label='org', description='test'
        )
        session.add(org)
    yield org


@pytest.fixture(scope='module', autouse=True)
def env(db, org: models.Organization) -> models.Environment:
    with db.scoped_session() as session:
        env = models.Environment(
            name='env',
            owner='me',
            organizationUri=org.organizationUri,
            label='env',
            AwsAccountId='1' * 12,
            region='eu-west-1',
            EnvironmentDefaultIAMRoleArn=f"arn:aws:iam::{'1'*12}:role/default_role",
            EnvironmentDefaultIAMRoleName='default_role',
            EnvironmentDefaultBucketName='envbucketbcuketenvbucketbcuketenvbucketbcuketenvbucketbcuket',
            EnvironmentDefaultAthenaWorkGroup='DefaultWorkGroup',
            CDKRoleArn='xxx',
            SamlGroupName='admins',
            subscriptionsEnabled=True,
            subscriptionsConsumersTopicName='topicname',
        )
        session.add(env)
        session.commit()
        env_group = models.EnvironmentGroup(
            environmentUri=env.environmentUri,
            groupUri=env.SamlGroupName,
            environmentIAMRoleArn=env.EnvironmentDefaultIAMRoleArn,
            environmentIAMRoleName=env.EnvironmentDefaultIAMRoleName,
            environmentAthenaWorkGroup='workgroup',
        )
        session.add(env_group)
        tags = models.KeyValueTag(
            targetType='environment',
            targetUri=env.environmentUri,
            key='CREATOR',
            value='customtagowner',
        )
        session.add(tags)
    yield env


@pytest.fixture(scope='module', autouse=True)
def another_group(db, env):
    with db.scoped_session() as session:
        env_group: models.EnvironmentGroup = models.EnvironmentGroup(
            environmentUri=env.environmentUri,
            groupUri='anothergroup',
            environmentIAMRoleArn='aontherGroupArn',
            environmentIAMRoleName='anotherGroupRole',
            environmentAthenaWorkGroup='workgroup',
        )
        session.add(env_group)
        dataset = models.Dataset(
            label='thisdataset',
            environmentUri=env.environmentUri,
            organizationUri=env.organizationUri,
            name='anotherdataset',
            description='test',
            AwsAccountId=env.AwsAccountId,
            region=env.region,
            S3BucketName='bucket',
            GlueDatabaseName='db',
            IAMDatasetAdminRoleArn='role',
            IAMDatasetAdminUserArn='xxx',
            KmsAlias='xxx',
            owner='me',
            confidentiality='C1',
            businessOwnerEmail='jeff',
            businessOwnerDelegationEmails=['andy'],
            SamlAdminGroupName=env_group.groupUri,
            GlueCrawlerName='dhCrawler',
        )
        session.add(dataset)
        yield env_group


@pytest.fixture(scope='module', autouse=True)
def dataset(db, env: models.Environment) -> models.Dataset:
    with db.scoped_session() as session:
        dataset = models.Dataset(
            label='thisdataset',
            environmentUri=env.environmentUri,
            organizationUri=env.organizationUri,
            name='thisdataset',
            description='test',
            AwsAccountId=env.AwsAccountId,
            region=env.region,
            S3BucketName='bucket',
            GlueDatabaseName='db',
            IAMDatasetAdminRoleArn='role',
            IAMDatasetAdminUserArn='xxx',
            KmsAlias='xxx',
            owner='me',
            confidentiality='C1',
            businessOwnerEmail='jeff',
            businessOwnerDelegationEmails=['andy'],
            SamlAdminGroupName='admins',
            GlueCrawlerName='dhCrawler',
        )
        session.add(dataset)
    yield dataset


@pytest.fixture(scope='module', autouse=True)
def table(db, dataset: models.Dataset) -> models.DatasetTable:
    with db.scoped_session() as session:
        table = models.DatasetTable(
            label='thistable',
            owner='me',
            datasetUri=dataset.datasetUri,
            AWSAccountId=dataset.AwsAccountId,
            region=dataset.region,
            GlueDatabaseName=dataset.GlueDatabaseName,
            S3BucketName=dataset.S3BucketName,
            GlueTableName='asimpletesttable',
            S3Prefix='/raw/asimpletesttable/',
        )

        session.add(table)
    yield table


@pytest.fixture(scope='module', autouse=True)
def sgm_studio(db, env: models.Environment) -> models.SagemakerStudioUserProfile:
    with db.scoped_session() as session:
        notebook = models.SagemakerStudioUserProfile(
            label='thistable',
            owner='me',
            AWSAccountId=env.AwsAccountId,
            region=env.region,
            sagemakerStudioUserProfileStatus='UP',
            sagemakerStudioUserProfileName='Profile',
            sagemakerStudioUserProfileNameSlugify='Profile',
            sagemakerStudioDomainID='domain',
            environmentUri=env.environmentUri,
            RoleArn=env.EnvironmentDefaultIAMRoleArn,
            SamlAdminGroupName='admins',
        )
        session.add(notebook)
    yield notebook


@pytest.fixture(scope='module', autouse=True)
def notebook(db, env: models.Environment) -> models.SagemakerNotebook:
    with db.scoped_session() as session:
        notebook = models.SagemakerNotebook(
            label='thistable',
            NotebookInstanceStatus='RUNNING',
            owner='me',
            AWSAccountId=env.AwsAccountId,
            region=env.region,
            environmentUri=env.environmentUri,
            RoleArn=env.EnvironmentDefaultIAMRoleArn,
            SamlAdminGroupName='admins',
            VolumeSizeInGB=32,
            InstanceType='ml.t3.medium',
        )
        session.add(notebook)
    yield notebook


@pytest.fixture(scope='module', autouse=True)
def pipeline1(db, env: models.Environment) -> models.DataPipeline:
    with db.scoped_session() as session:
        pipeline = models.DataPipeline(
            label='thistable',
            owner='me',
            AwsAccountId=env.AwsAccountId,
            region=env.region,
            environmentUri=env.environmentUri,
            repo='pipeline',
            SamlGroupName='admins',
            devStrategy='cdk-trunk'
        )
        session.add(pipeline)
    yield pipeline


@pytest.fixture(scope='module', autouse=True)
def pipeline2(db, env: models.Environment) -> models.DataPipeline:
    with db.scoped_session() as session:
        pipeline = models.DataPipeline(
            label='thistable',
            owner='me',
            AwsAccountId=env.AwsAccountId,
            region=env.region,
            environmentUri=env.environmentUri,
            repo='pipeline',
            SamlGroupName='admins',
            devStrategy='trunk'
        )
        session.add(pipeline)
    yield pipeline


@pytest.fixture(scope='module', autouse=True)
def pip_envs(db, env: models.Environment, pipeline1: models.DataPipeline) -> models.DataPipelineEnvironment:
    with db.scoped_session() as session:
        pipeline_env1 = models.DataPipelineEnvironment(
            owner='me',
            label=f"{pipeline1.label}-{env.label}",
            environmentUri=env.environmentUri,
            environmentLabel=env.label,
            pipelineUri=pipeline1.DataPipelineUri,
            pipelineLabel=pipeline1.label,
            envPipelineUri=f"{pipeline1.DataPipelineUri}{env.environmentUri}",
            AwsAccountId=env.AwsAccountId,
            region=env.region,
            stage='dev',
            order=1,
            samlGroupName='admins'
        )

        session.add(pipeline_env1)

    yield api.Pipeline.query_pipeline_environments(session=session, uri=pipeline1.DataPipelineUri)

@pytest.fixture(scope='module', autouse=True)
def redshift_cluster(db, env: models.Environment) -> models.RedshiftCluster:
    with db.scoped_session() as session:
        cluster = models.RedshiftCluster(
            environmentUri=env.environmentUri,
            organizationUri=env.organizationUri,
            owner='owner',
            label='cluster',
            description='desc',
            masterDatabaseName='dev',
            masterUsername='masteruser',
            databaseName='datahubdb',
            nodeType='dc1.large',
            numberOfNodes=2,
            port=5432,
            region=env.region,
            AwsAccountId=env.AwsAccountId,
            status='CREATING',
            vpc='vpc-12344',
            IAMRoles=[env.EnvironmentDefaultIAMRoleArn],
            tags=[],
            SamlGroupName='admins',
            imported=False,
        )
        session.add(cluster)
    yield cluster


@pytest.fixture(scope='function', autouse=True)
def patch_ssm(mocker):
    mocker.patch(
        'dataall.utils.parameter.Parameter.get_parameter', return_value='param'
    )
