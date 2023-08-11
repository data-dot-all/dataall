import pytest

from dataall.modules.worksheets.api.resolvers import WorksheetRole


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
