import pytest
from dataall.api.constants import WorksheetRole


@pytest.fixture(scope='module', autouse=True)
def worksheet(client, tenant, group):
    response = client.query(
        """
        mutation CreateWorksheet ($input:NewWorksheetInput){
            createWorksheet(input:$input){
                worksheetUri
                label
                description
                tags
                owner
                userRoleForWorksheet
            }
        }
        """,
        input={
            'label': 'my worksheet',
            'SamlAdminGroupName': group.name,
            'tags': [group.name],
        },
        username='alice',
        groups=[group.name],
        tags=[group.name],
    )
    return response.data.createWorksheet


def test_create_worksheet(client, worksheet):
    assert worksheet.label == 'my worksheet'
    assert worksheet.owner == 'alice'
    assert worksheet.userRoleForWorksheet == WorksheetRole.Creator.name


def test_list_worksheets_as_creator(client, group):
    response = client.query(
        """
        query ListWorksheets ($filter:WorksheetFilter){
            listWorksheets (filter:$filter){
                count
                page
                pages
                nodes{
                    worksheetUri
                    label
                    description
                    tags
                    owner
                    userRoleForWorksheet
                }
            }
        }
        """,
        filter={'page': 1},
        username='alice',
        groups=[group.name],
    )

    assert response.data.listWorksheets.count == 1


def test_list_worksheets_as_anonymous(client, group):
    response = client.query(
        """
        query ListWorksheets ($filter:WorksheetFilter){
            listWorksheets (filter:$filter){
                count
                page
                pages
                nodes{
                    worksheetUri
                    label
                    description
                    tags
                    owner
                    userRoleForWorksheet
                }
            }
        }
        """,
        filter={'page': 1},
        username='anonymous',
    )

    print(response)
    assert response.data.listWorksheets.count == 0


def test_get_worksheet(client, worksheet, group):
    response = client.query(
        """
            query GetWorksheet($worksheetUri:String!){
                getWorksheet(worksheetUri:$worksheetUri){
                    label
                    description
                    userRoleForWorksheet
                }
            }
        """,
        worksheetUri=worksheet.worksheetUri,
        username='alice',
        groups=[group.name],
    )

    assert response.data.getWorksheet.userRoleForWorksheet == WorksheetRole.Creator.name

    response = client.query(
        """
            query GetWorksheet($worksheetUri:String!){
                getWorksheet(worksheetUri:$worksheetUri){
                    label
                    description
                    userRoleForWorksheet
                }
            }
        """,
        worksheetUri=worksheet.worksheetUri,
        username='anonymous',
    )

    assert 'Unauthorized' in response.errors[0].message


def test_update_worksheet(client, worksheet, group):
    response = client.query(
        """
        mutation UpdateWorksheet($worksheetUri:String!, $input:UpdateWorksheetInput){
            updateWorksheet(
                worksheetUri:$worksheetUri,
                input:$input
            ){
                worksheetUri
                label
            }
        }
        """,
        worksheetUri=worksheet.worksheetUri,
        input={'label': 'change label'},
        username='alice',
        groups=[group.name],
    )

    assert response.data.updateWorksheet.label == 'change label'


def test_share_with_individual(client, worksheet, group2, group):
    response = client.query(
        """
        mutation ShareWorksheet(
            $worksheetUri:String!,
            $input: WorksheetShareInput!
        ){
            shareWorksheet(worksheetUri:$worksheetUri,input:$input){
                worksheetShareUri
                canEdit
            }
        }
        """,
        worksheetUri=worksheet.worksheetUri,
        input={'principalId': group2.name, 'principalType': 'Group', 'canEdit': False},
        username='alice',
        groups=[group.name],
    )
    share_uri = response.data.shareWorksheet.worksheetShareUri
    assert share_uri
    assert not response.data.shareWorksheet.canEdit

    response = client.query(
        """
        mutation UpdateShareWorksheet(
            $worksheetShareUri:String!,
            $canEdit: Boolean!
        ){
            updateShareWorksheet(worksheetShareUri:$worksheetShareUri,canEdit:$canEdit){
                worksheetShareUri
                canEdit
            }
        }
        """,
        worksheetShareUri=share_uri,
        canEdit=True,
        username='alice',
        groups=[group.name],
    )
    share_uri = response.data.updateShareWorksheet.worksheetShareUri
    assert share_uri
    assert response.data.updateShareWorksheet.canEdit

    response = client.query(
        """
            query GetWorksheet($worksheetUri:String!){
                getWorksheet(worksheetUri:$worksheetUri){
                    label
                    description
                    userRoleForWorksheet
                }
            }
        """,
        worksheetUri=worksheet.worksheetUri,
        username='bob',
        groups=[group2.name],
    )

    assert response.data.getWorksheet.label == 'change label'

    response = client.query(
        """
            query GetWorksheet($worksheetUri:String!){
                getWorksheet(worksheetUri:$worksheetUri){
                    label
                    description
                    userRoleForWorksheet
                    shares{
                        count
                    }
                    lastSavedQueryResult
                    {
                        AthenaQueryId
                    }

                }
            }
        """,
        worksheetUri=worksheet.worksheetUri,
        username='bob',
        groups=[group2.name],
    )

    assert response.data.getWorksheet.label == 'change label'

    response = client.query(
        """
        mutation deleteShareWorksheet(
            $worksheetShareUri:String!
        ){
            deleteShareWorksheet(worksheetShareUri:$worksheetShareUri)
        }
        """,
        worksheetShareUri=share_uri,
        username='alice',
        groups=[group.name],
    )
    assert response.data.deleteShareWorksheet

    response = client.query(
        """
            query GetWorksheet($worksheetUri:String!){
                getWorksheet(worksheetUri:$worksheetUri){
                    label
                    description
                    userRoleForWorksheet
                }
            }
        """,
        worksheetUri=worksheet.worksheetUri,
        username='bob',
        groups=[group2.name],
    )

    assert 'UnauthorizedOperation' in response.errors[0].message

    response = client.query(
        """
        mutation deleteWorksheet(
            $worksheetUri:String!
        ){
            deleteWorksheet(worksheetUri:$worksheetUri)
        }
        """,
        worksheetUri=worksheet.worksheetUri,
        username='alice',
        groups=[group.name],
    )
    assert response.data.deleteWorksheet
