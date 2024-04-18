"""
DAO layer that encapsulates the logic and interaction with the database for maintenance
"""

from dataall.modules.maintenance.db.maintenance_models import Maintenance


class MaintenanceRepository:

    def __init__(self, session):
        self._session = session

    def save_maintenance_status_and_mode(self, maintenance_status: str, maintenance_mode: str):
        maintenance_record = self._session.query(Maintenance)
        maintenance_record.status = maintenance_status
        maintenance_record.mode = maintenance_mode
        self._session.commit()

    def get_maintenance_record(self):
        return self._session.query(Maintenance)

    def get_maintenance_mode(self):
        maintenance_record = self._session.query(Maintenance)
        return maintenance_record.mode

