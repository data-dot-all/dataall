"""
A service layer for maintenance activity
Defines functions and business logic to be performed for maintenance window
"""

import logging
import os

from dataall.base.aws.event_bridge import EventBridge
from dataall.base.aws.parameter_store import ParameterStoreManager
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyValidationService
from dataall.modules.maintenance.api.enums import MaintenanceStatus
from dataall.modules.maintenance.db.maintenance_repository import MaintenanceRepository
from dataall.core.stacks.aws.ecs import Ecs

logger = logging.getLogger(__name__)


class MaintenanceService:
    @staticmethod
    def start_maintenance_window(engine, mode: str = None, groups=None):
        """
        Start maintenance window by performing following actions
            1. Perform validation to check if the user belongs to the DAAdministrators group
            2. Put the maintenance window status to PENDING and update the maintenance mode
            3. Get all the ECS Scheduled tasks and disable the schedule for them
        @param engine: db engine
        @param mode: mode to set for maintenance window
        @param groups: user groups from context.groups
        @return: returns True if successful or False
        """
        # Check from the context if the groups contains the DAAAdminstrators group
        if groups is None:
            groups = []
        if not TenantPolicyValidationService.is_tenant_admin(groups):
            raise Exception('Only data.all admin group members can start maintenance window')

        logger.info('Putting data.all into maintenance')
        try:
            with engine.scoped_session() as session:
                maintenance_record = MaintenanceRepository(session).get_maintenance_record()
                if (
                    maintenance_record.status == MaintenanceStatus.PENDING.value
                    or maintenance_record.status == MaintenanceStatus.ACTIVE.value
                ):
                    logger.error(
                        'Maintenance window already in PENDING or ACTIVE state. Cannot start maintenance window. Stop the maintenance window and start again'
                    )
                    return False
                MaintenanceRepository(session).save_maintenance_status_and_mode(
                    maintenance_status=MaintenanceStatus.PENDING.value, maintenance_mode=mode
                )
            # Disable scheduled ECS tasks
            # Get all the SSM Params related to the scheduled tasks
            ecs_scheduled_rules = ParameterStoreManager.get_parameters_by_path(
                region=os.getenv('AWS_REGION', 'eu-west-1'),
                parameter_path=f"/dataall/{os.getenv('envname', 'local')}/ecs/ecs_scheduled_tasks/rule",
            )
            logger.debug(ecs_scheduled_rules)
            ecs_scheduled_rules_list = [item['Value'] for item in ecs_scheduled_rules]
            event_bridge_session = EventBridge(region=os.getenv('AWS_REGION', 'eu-west-1'))
            event_bridge_session.disable_scheduled_ecs_tasks(ecs_scheduled_rules_list)
            return True
        except Exception as e:
            logger.error(f'Error occurred while starting maintenance window due to {e}')
            return False

    @staticmethod
    def stop_maintenance_window(engine, groups=None):
        """
        Stop maintenance window by performing following actions
            1. Perform validation to check if the user belongs to the DAAdministrators group
            2. Update the RDS table by changing the status to INACTIVE and mode to '-'
            3. Enable all data.all related ECS scheduled tasks
        @param engine: db engine
        @param groups: user groups from context.groups
        @return: return True if successful or False
        """

        # Check from the context if the groups contains the DAAAdminstrators group
        if groups is None:
            groups = []
        if not TenantPolicyValidationService.is_tenant_admin(groups):
            raise Exception('Only data.all admin group members can stop maintenance window')
        logger.info('Stopping maintenance mode')
        try:
            with engine.scoped_session() as session:
                maintenance_record = MaintenanceRepository(session).get_maintenance_record()
                if maintenance_record.status == MaintenanceStatus.INACTIVE.value:
                    logger.error('Maintenance window already in INACTIVE state. Cannot stop maintenance window')
                    return False
                MaintenanceRepository(session).save_maintenance_status_and_mode(
                    maintenance_status='INACTIVE', maintenance_mode=''
                )
            # Enable scheduled ECS tasks
            ecs_scheduled_rules = ParameterStoreManager.get_parameters_by_path(
                region=os.getenv('AWS_REGION', 'eu-west-1'),
                parameter_path=f"/dataall/{os.getenv('envname', 'local')}/ecs/ecs_scheduled_tasks/rule",
            )
            logger.debug(ecs_scheduled_rules)
            ecs_scheduled_rules_list = [item['Value'] for item in ecs_scheduled_rules]
            event_bridge_session = EventBridge(region=os.getenv('AWS_REGION', 'eu-west-1'))
            event_bridge_session.enable_scheduled_ecs_tasks(ecs_scheduled_rules_list)
            return True
        except Exception as e:
            logger.error(f'Error occurred while stopping maintenance window due to {e}')
            return False

    @staticmethod
    def get_maintenance_window_status(engine):
        """
        Get the status of maintenance window
        Maintenance record is returned after checking if all ECS tasks in the data.all created cluster have completed.
        @param engine: db object
        @return: Maintenance object containing status and mode
        """
        logger.info('Checking maintenance window status')
        try:
            with engine.scoped_session() as session:
                maintenance_record = MaintenanceRepository(session).get_maintenance_record()
                if maintenance_record.status == MaintenanceStatus.PENDING.value:
                    # Check if ECS tasks are running
                    ecs_cluster_name = ParameterStoreManager.get_parameter_value(
                        region=os.getenv('AWS_REGION', 'eu-west-1'),
                        parameter_path=f"/dataall/{os.getenv('envname', 'local')}/ecs/cluster/name",
                    )
                    if Ecs.is_task_running(cluster_name=ecs_cluster_name):
                        logger.info(f'Current maintenance window status - {maintenance_record.status}')
                        return maintenance_record
                    else:
                        logger.info(
                            'All pending ECS tasks have completed running. Setting Maintenance Status to ACTIVE'
                        )
                        maintenance_record.status = MaintenanceStatus.ACTIVE.value
                        session.commit()
                        return maintenance_record
                else:
                    logger.info(f'Current maintenance window status - {maintenance_record.status}')
                    return maintenance_record
        except Exception as e:
            logger.error(f'Error while getting maintenance window status due to {e}')
            raise e

    # Fetches the mode of maintenance window
    @staticmethod
    def _get_maintenance_window_mode(engine):
        logger.info('Fetching mode of maintenance window')
        try:
            with engine.scoped_session() as session:
                maintenance_record = MaintenanceRepository(session).get_maintenance_record()
                return maintenance_record.mode
        except Exception as e:
            logger.error(f'Error while getting maintenance window mode due to {e}')
            raise e
