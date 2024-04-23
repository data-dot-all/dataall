"""
A service layer for sagemaker notebooks
Central part for working with notebooks
"""

import dataclasses
import logging
import os
from dataclasses import dataclass, field
from typing import List, Dict

from dataall.base.aws.event_bridge import EventBridge
from dataall.base.aws.parameter_store import ParameterStoreManager
from dataall.base.context import get_context as context
from dataall.core.environment.db.environment_models import Environment
from dataall.core.environment.env_permission_checker import has_group_permission
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.stacks.api import stack_helper
from dataall.core.stacks.db.keyvaluetag_repositories import KeyValueTag
from dataall.core.stacks.db.stack_repositories import Stack
from dataall.base.db import exceptions
from dataall.modules.maintenance.api.enums import MaintenanceStatus
from dataall.modules.maintenance.db.maintenance_repository import MaintenanceRepository
from dataall.modules.notebooks.aws.sagemaker_notebook_client import client
from dataall.modules.notebooks.db.notebook_models import SagemakerNotebook
from dataall.modules.notebooks.db.notebook_repository import NotebookRepository
from dataall.modules.notebooks.services.notebook_permissions import (
    MANAGE_NOTEBOOKS,
    CREATE_NOTEBOOK,
    NOTEBOOK_ALL,
    GET_NOTEBOOK,
    UPDATE_NOTEBOOK,
    DELETE_NOTEBOOK,
)
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from dataall.base.utils import slugify

logger = logging.getLogger(__name__)


class MaintenanceService:

    @staticmethod
    def start_maintenance_window(engine, mode: str = None):
        # Update the RDS table with the mode and status to PENDING
        logger.info("Putting data.all into maintenance")
        try:
            with engine.scoped_session() as session:
                # Todo:  Check the current status of maintenance mode and then execute the update query
                maintenance_record = MaintenanceRepository(session).get_maintenance_record()
                if maintenance_record.status == MaintenanceStatus.PENDING or maintenance_record.status == MaintenanceStatus.ACTIVE:
                    logger.error("Maintenance window already in PENDING or ACTIVE state. Cannot start maintenance window. Stop the maintenance window and start again")
                    return False
                MaintenanceRepository(session).save_maintenance_status_and_mode(maintenance_status=MaintenanceStatus.PENDING ,maintenance_mode=mode)
            # Disable scheduled ECS tasks
            # Get all the SSMs related to the scheduled tasks
            ecs_scheduled_rules = ParameterStoreManager.get_parameters_by_path(
                region=os.getenv('AWS_REGION', 'eu-west-1'),
                parameter_path=f"/dataall/{os.getenv('envname', 'local')}/ecs/ecs_scheduled_tasks/rule"
            )
            logger.info(ecs_scheduled_rules)
            ecs_scheduled_rules_list = [item['Value'] for item in ecs_scheduled_rules]
            logger.info("Value of ecs scheduled tasks")
            logger.info(ecs_scheduled_rules_list)
            event_bridge_session = EventBridge(region=os.getenv('AWS_REGION', 'eu-west-1'))
            event_bridge_session.disable_scheduled_ecs_tasks(ecs_scheduled_rules_list)
            return True
        except Exception as e:
            logger.error(f"Error occurred while starting maintenance window due to {e}")
            return False

    @staticmethod
    def stop_maintenance_window(engine):
        # Update the RDS table by changing mode to - ''
        # Update the RDS table by changing the status to INACTIVE
        logger.info("Stopping maintenance")
        try:
            with engine.scoped_session() as session:
                maintenance_record = MaintenanceRepository(session).get_maintenance_record()
                if maintenance_record.status == MaintenanceStatus.PENDING or maintenance_record.status == MaintenanceStatus.INACTIVE:
                    logger.error("Maintenance window already in PENDING or INACTIVE state. Cannot start maintenance window. Stop the maintenance window and start again")
                    return False
                MaintenanceRepository(session).save_maintenance_status_and_mode(maintenance_status='INACTIVE', maintenance_mode='')
            # Enable scheduled ECS tasks
            ecs_scheduled_rules = ParameterStoreManager.get_parameters_by_path(
                region=os.getenv('AWS_REGION', 'eu-west-1'),
                parameter_path=f"/dataall/{os.getenv('envname', 'local')}/ecs/ecs_scheduled_tasks/rule"
            )
            logger.info(ecs_scheduled_rules)
            ecs_scheduled_rules_list = [item['Value'] for item in ecs_scheduled_rules]
            logger.info("Value of ecs scheduled tasks")
            logger.info(ecs_scheduled_rules_list)
            event_bridge_session = EventBridge()
            event_bridge_session.enable_scheduled_ecs_tasks(ecs_scheduled_rules_list)
            return True
        except Exception as e:
            logger.error(f"Error occurred while stopping maintenance window due to {e}")
            return False


    @staticmethod
    def get_maintenance_window_status(engine):
        logger.info("Checking maintenance window status")
        with engine.scoped_session() as session:
            maintenance_record = MaintenanceRepository(session).get_maintenance_record()
            if maintenance_record.status == MaintenanceStatus.PENDING:
                # Check all the ECS tasks
                return False
                # Fetch the name of ECS services



    @staticmethod
    def get_maintenance_window_mode():
        logger.info("Gettting the maintenance window mode")
        return "READ-ONLY"
