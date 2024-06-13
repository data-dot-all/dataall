from dataall.modules.mlstudio.db.mlstudio_models import SagemakerStudioUser


def test_create_sagemaker_studio_domain(
    db, client, org_fixture, env_with_mlstudio, user, group, vpcId='vpc-1234', subnetIds=['subnet']
):
    response = client.query(
        """
        query getEnvironmentMLStudioDomain($environmentUri: String!) {
          getEnvironmentMLStudioDomain(environmentUri: $environmentUri) {
            sagemakerStudioUri
            environmentUri
            label
            sagemakerStudioDomainName
            DefaultDomainRoleName
            vpcType
            vpcId
            subnetIds
            owner
            created
          }
        }
        """,
        environmentUri=env_with_mlstudio.environmentUri,
    )

    assert response.data.getEnvironmentMLStudioDomain.sagemakerStudioUri
    assert response.data.getEnvironmentMLStudioDomain.label == f'{env_with_mlstudio.label}-domain'
    assert response.data.getEnvironmentMLStudioDomain.vpcType == 'created'
    assert len(response.data.getEnvironmentMLStudioDomain.vpcId) == 0
    assert len(response.data.getEnvironmentMLStudioDomain.subnetIds) == 0
    assert response.data.getEnvironmentMLStudioDomain.environmentUri == env_with_mlstudio.environmentUri


def test_create_sagemaker_studio_user(sagemaker_studio_user, group, env_with_mlstudio):
    """Testing that the conftest sagemaker studio user has been created correctly"""
    assert sagemaker_studio_user.label == 'testcreate'
    assert sagemaker_studio_user.SamlAdminGroupName == group.name
    assert sagemaker_studio_user.environmentUri == env_with_mlstudio.environmentUri


def test_list_sagemaker_studio_users(client, db, group, multiple_sagemaker_studio_users):
    response = client.query(
        """
        query listSagemakerStudioUsers($filter:SagemakerStudioUserFilter!){
            listSagemakerStudioUsers(filter:$filter){
                count
                nodes{
                    sagemakerStudioUserUri
                }
            }
        }
        """,
        filter={},
        username='alice',
    )
    print(response.data)
    assert len(response.data.listSagemakerStudioUsers['nodes']) == 10


def test_nopermissions_list_sagemaker_studio_users(client, db, group):
    response = client.query(
        """
        query listSagemakerStudioUsers($filter:SagemakerStudioUserFilter!){
            listSagemakerStudioUsers(filter:$filter){
                count
                nodes{
                    sagemakerStudioUserUri
                }
            }
        }
        """,
        filter={},
        username='bob',
    )
    assert len(response.data.listSagemakerStudioUsers['nodes']) == 0


def test_delete_sagemaker_studio_user(client, db, group, sagemaker_studio_user):
    response = client.query(
        """
        mutation deleteSagemakerStudioUser($sagemakerStudioUserUri:String!, $deleteFromAWS:Boolean){
            deleteSagemakerStudioUser(sagemakerStudioUserUri:$sagemakerStudioUserUri, deleteFromAWS:$deleteFromAWS)
        }
        """,
        sagemakerStudioUserUri=sagemaker_studio_user.sagemakerStudioUserUri,
        deleteFromAWS=True,
        username='alice',
        groups=[group.name],
    )
    assert response.data
    with db.scoped_session() as session:
        n = session.query(SagemakerStudioUser).get(sagemaker_studio_user.sagemakerStudioUserUri)
        assert not n


def update_env_query():
    query = """
        mutation UpdateEnv($environmentUri:String!,$input:ModifyEnvironmentInput!){
            updateEnvironment(environmentUri:$environmentUri,input:$input){
                organization{
                    organizationUri
                }
                label
                AwsAccountId
                region
                SamlGroupName
                owner
                tags
                resourcePrefix
                parameters {
                    key
                    value
                }
            }
        }
    """
    return query


def test_update_env_delete_domain(client, org_fixture, env_with_mlstudio, group, group2):
    response = client.query(
        update_env_query(),
        username='alice',
        environmentUri=env_with_mlstudio.environmentUri,
        input={
            'label': 'DEV',
            'tags': [],
            'parameters': [{'key': 'mlStudiosEnabled', 'value': 'False'}],
        },
        groups=[group.name],
    )

    response = client.query(
        """
        query getEnvironmentMLStudioDomain($environmentUri: String!) {
          getEnvironmentMLStudioDomain(environmentUri: $environmentUri) {
            sagemakerStudioUri
            environmentUri
            label
            sagemakerStudioDomainName
            DefaultDomainRoleName
            vpcType
            vpcId
            subnetIds
            owner
            created
          }
        }
        """,
        environmentUri=env_with_mlstudio.environmentUri,
    )
    assert response.data.getEnvironmentMLStudioDomain is None


def test_update_env_create_domain_with_vpc(db, client, org_fixture, env_with_mlstudio, user, group):
    response = client.query(
        update_env_query(),
        username='alice',
        environmentUri=env_with_mlstudio.environmentUri,
        input={
            'label': 'dev',
            'tags': [],
            'vpcId': 'vpc-12345',
            'subnetIds': ['subnet-12345', 'subnet-67890'],
            'parameters': [{'key': 'mlStudiosEnabled', 'value': 'True'}],
        },
        groups=[group.name],
    )

    response = client.query(
        """
        query getEnvironmentMLStudioDomain($environmentUri: String!) {
          getEnvironmentMLStudioDomain(environmentUri: $environmentUri) {
            sagemakerStudioUri
            environmentUri
            label
            sagemakerStudioDomainName
            DefaultDomainRoleName
            vpcType
            vpcId
            subnetIds
            owner
            created
          }
        }
        """,
        environmentUri=env_with_mlstudio.environmentUri,
    )

    assert response.data.getEnvironmentMLStudioDomain.sagemakerStudioUri
    assert response.data.getEnvironmentMLStudioDomain.label == f'{env_with_mlstudio.label}-domain'
    assert response.data.getEnvironmentMLStudioDomain.vpcType == 'imported'
    assert response.data.getEnvironmentMLStudioDomain.vpcId == 'vpc-12345'
    assert len(response.data.getEnvironmentMLStudioDomain.subnetIds) == 2
    assert response.data.getEnvironmentMLStudioDomain.environmentUri == env_with_mlstudio.environmentUri
