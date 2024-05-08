from unittest.mock import MagicMock
from dataall.base.config import config

import pytest

from dataall.modules.maintenance.db.maintenance_models import Maintenance


@pytest.fixture(scope='module')
def mock_ecs_client(module_mocker):
    module_mocker.patch(
        'dataall.modules.maintenance.services.maintenance_service.ParameterStoreManager.get_parameters_by_path',
        return_value=[{'item': 'task1', 'Value': 'task1'}, {'item': 'task2', 'Value': 'task2'}],
    )
    mock_events = MagicMock()
    module_mocker.patch(
        'dataall.modules.maintenance.services.maintenance_service.EventBridge', return_value=mock_events
    )
    mock_events().disable_scheduled_ecs_tasks.return_value = True
    yield mock_events


@pytest.fixture(scope='function')
def init_maintenance_record(db):
    with db.scoped_session() as session:
        maintenance_record = Maintenance(status='INACTIVE', mode='')
        session.add(maintenance_record)
        session.commit()
    yield
    with db.scoped_session() as session:
        maintenance_record = session.query(Maintenance).one()
        session.delete(maintenance_record)
        session.commit()


def test_start_maintenance_window(db, client, mock_ecs_client, init_maintenance_record):
    response = client.query(
        """
        mutation startMaintenanceWindow($mode: String!){
            startMaintenanceWindow(mode: $mode)
        }
        """,
        mode='READ-ONLY',
        username='alice',
        groups=['DAAdministrators', 'Engineers'],
    )

    assert response
    assert response.data.startMaintenanceWindow is True

    with db.scoped_session() as session:
        maintenance_record = session.query(Maintenance).one()
        assert maintenance_record.status == 'PENDING'
        assert maintenance_record.mode == 'READ-ONLY'


def test_start_maintenance_window_with_team_not_a_data_admin(client, mock_ecs_client, init_maintenance_record):
    response = client.query(
        """
        mutation startMaintenanceWindow($mode: String!){
            startMaintenanceWindow(mode: $mode)
        }
        """,
        mode='READ-ONLY',
        username='alice',
        groups=['Engineers'],
    )

    assert response
    assert 'Only data.all admin group members can start maintenance window' in response.errors[0]['message']


def test_stop_maintenance_window(db, client, mock_ecs_client, init_maintenance_record):
    # Initialize the maintenance window with ACTIVE status and READ-ONLY mode
    with db.scoped_session() as session:
        maintenance_record = session.query(Maintenance).one()
        maintenance_record.mode = 'READ-ONLY'
        maintenance_record.status = 'ACTIVE'
        session.add(maintenance_record)
        session.commit()

    response = client.query(
        """
            mutation stopMaintenanceWindow{
                stopMaintenanceWindow
            }
            """,
        username='alice',
        groups=['DAAdministrators', 'Engineers'],
    )

    assert response
    assert response.data.stopMaintenanceWindow is True


def test_stop_maintenance_window_no_dataall_admin(db, client, mock_ecs_client, init_maintenance_record):
    # Initialize the maintenance window with ACTIVE status and READ-ONLY mode
    with db.scoped_session() as session:
        maintenance_record = session.query(Maintenance).one()
        maintenance_record.mode = 'READ-ONLY'
        maintenance_record.status = 'ACTIVE'
        session.add(maintenance_record)
        session.commit()

    response = client.query(
        """
            mutation stopMaintenanceWindow{
                stopMaintenanceWindow
            }
            """,
        username='alice',
        groups=['Engineers'],
    )

    assert response
    assert 'Only data.all admin group members can stop maintenance window' in response.errors[0]['message']


def test_get_maintenance_window_status(db, client, mock_ecs_client, init_maintenance_record):
    # Initialize the maintenance window with ACTIVE status and READ-ONLY mode
    with db.scoped_session() as session:
        maintenance_record = session.query(Maintenance).one()
        maintenance_record.mode = 'READ-ONLY'
        maintenance_record.status = 'ACTIVE'
        session.add(maintenance_record)
        session.commit()

    response = client.query(
        """
               query getMaintenanceWindowStatus{
                   getMaintenanceWindowStatus{
                    status,
                    mode
                   }
               }
               """,
        username='alice',
        groups=['DAAdministrators', 'Engineers'],
    )

    assert response
    assert response.data.getMaintenanceWindowStatus.status == 'ACTIVE'
    assert response.data.getMaintenanceWindowStatus.mode == 'READ-ONLY'
