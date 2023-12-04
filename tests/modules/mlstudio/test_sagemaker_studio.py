from dataall.modules.mlstudio.db.mlstudio_models import SagemakerStudioUser


def test_create_sagemaker_studio_domain(sagemaker_studio_domain, env_fixture):
    """Testing that the conftest sagemaker studio domain has been created correctly"""
    assert sagemaker_studio_domain.label == 'testcreate-domain'
    assert sagemaker_studio_domain.vpcType == 'created'
    assert sagemaker_studio_domain.vpcId is None
    assert len(sagemaker_studio_domain.subnetIds) == 0
    assert sagemaker_studio_domain.environmentUri == env_fixture.environmentUri


def test_create_sagemaker_studio_domain_unauthorized(client, env_fixture, group2):
    response = client.query(
        """
            mutation createMLStudioDomain($input: NewStudioDomainInput) {
              createMLStudioDomain(input: $input) {
                sagemakerStudioUri
                environmentUri
                label
                vpcType
                vpcId
                subnetIds
              }
            }
            """,
        input={
            'label': 'testcreate',
            'environmentUri': env_fixture.environmentUri,
        },
        username='anonymoususer',
        groups=[group2.name],
    )
    assert 'Unauthorized' in response.errors[0].message


def test_create_sagemaker_studio_user(sagemaker_studio_user, group, env_fixture):
    """Testing that the conftest sagemaker studio user has been created correctly"""
    assert sagemaker_studio_user.label == 'testcreate'
    assert sagemaker_studio_user.SamlAdminGroupName == group.name
    assert sagemaker_studio_user.environmentUri == env_fixture.environmentUri


def test_list_sagemaker_studio_users(client, env_fixture, db, group, multiple_sagemaker_studio_users):
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


def test_nopermissions_list_sagemaker_studio_users(
    client, db, group
):
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


def test_delete_sagemaker_studio_user(
    client, db, group, sagemaker_studio_user
):
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
        n = session.query(SagemakerStudioUser).get(
            sagemaker_studio_user.sagemakerStudioUserUri
        )
        assert not n


def test_get_sagemaker_studio_domain(client, env_fixture, sagemaker_studio_domain):
    response = client.query(
        """
        query getEnvironmentMLStudioDomain($environmentUri: String) {
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
        environmentUri=env_fixture.environmentUri,
    )
    print(response.data)
    assert response.data.getEnvironmentMLStudioDomain.sagemakerStudioUri == sagemaker_studio_domain.sagemakerStudioUri


def test_delete_sagemaker_studio_domain(client, env_fixture, group):
    response = client.query(
        """
        mutation deleteEnvironmentMLStudioDomain($environmentUri: String!) {
          deleteEnvironmentMLStudioDomain(environmentUri: $environmentUri)
        }
        """,
        environmentUri=env_fixture.environmentUri,
        username='alice',
        groups=[group.name],
    )
    assert response.data.deleteEnvironmentMLStudioDomain

    response = client.query(
        """
        query getEnvironmentMLStudioDomain($environmentUri: String) {
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
        environmentUri=env_fixture.environmentUri
    )
    assert response.data.getEnvironmentMLStudioDomain is None


def test_create_sagemaker_studio_domain_with_vpc(sagemaker_studio_domain_with_vpc, env_fixture):
    """Testing that the conftest sagemaker studio domain has been created correctly"""
    assert sagemaker_studio_domain_with_vpc.label == 'testcreate-domain'
    assert sagemaker_studio_domain_with_vpc.vpcType == 'imported'
    assert sagemaker_studio_domain_with_vpc.vpcId == 'vpc-12345'
    assert sagemaker_studio_domain_with_vpc.subnetIds == ['subnet-12345', 'subnet-67890']
    assert sagemaker_studio_domain_with_vpc.environmentUri == env_fixture.environmentUri


def test_delete_sagemaker_studio_domain_unauthorized(client, env_fixture, group2):
    response = client.query(
        """
        mutation deleteEnvironmentMLStudioDomain($environmentUri: String!) {
          deleteEnvironmentMLStudioDomain(environmentUri: $environmentUri)
        }
        """,
        environmentUri=env_fixture.environmentUri,
        username='anonymoususer',
        groups=[group2.name],
    )

    assert 'Unauthorized' in response.errors[0].message
