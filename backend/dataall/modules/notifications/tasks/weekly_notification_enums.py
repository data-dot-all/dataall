from enum import Enum

from dataall.core.stacks.api.enums import StackStatus


class ResourceStatus(Enum):
    PENDINGAPPROVAL = 'Submitted - Pending Approval'
    HEALTHY = 'Healthy'
    UNHEALTHY = 'Unhealthy'
    CREATE_FAILED = StackStatus.CREATE_FAILED.value
    DELETE_FAILED = StackStatus.DELETE_FAILED.value
    UPDATE_FAILED = StackStatus.UPDATE_FAILED.value
    UPDATE_ROLLBACK_FAILED = StackStatus.UPDATE_ROLLBACK_FAILED.value
    ROLLBACK_FAILED = StackStatus.ROLLBACK_FAILED.value


class ResourceType(Enum):
    SHAREOBJECT = 'Share Object'
    DATASET = 'Dataset'
    ENVIRONMENT = 'Environment'
