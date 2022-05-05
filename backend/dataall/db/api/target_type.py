import logging

from .. import exceptions, permissions
from .. import models

logger = logging.getLogger(__name__)


class TargetType:
    @staticmethod
    def get_target_type_permissions():
        return dict(
            dataset=(permissions.GET_DATASET, permissions.UPDATE_DATASET),
            environment=(permissions.GET_ENVIRONMENT, permissions.UPDATE_ENVIRONMENT),
            notebook=(permissions.GET_NOTEBOOK, permissions.UPDATE_NOTEBOOK),
            mlstudio=(
                permissions.GET_SGMSTUDIO_NOTEBOOK,
                permissions.UPDATE_SGMSTUDIO_NOTEBOOK,
            ),
            pipeline=(permissions.GET_PIPELINE, permissions.UPDATE_PIPELINE),
            redshift=(
                permissions.GET_REDSHIFT_CLUSTER,
                permissions.GET_REDSHIFT_CLUSTER,
            ),
        )

    @staticmethod
    def get_resource_update_permission_name(target_type):
        TargetType.is_supported_target_type(target_type)
        return TargetType.get_target_type_permissions()[target_type][1]

    @staticmethod
    def get_resource_read_permission_name(target_type):
        TargetType.is_supported_target_type(target_type)
        return TargetType.get_target_type_permissions()[target_type][0]

    @staticmethod
    def is_supported_target_type(target_type):
        supported_types = [
            "dataset",
            "environment",
            "notebook",
            "mlstudio",
            "pipeline",
            "redshift",
        ]
        if target_type not in supported_types:
            raise exceptions.InvalidInput(
                "targetType",
                target_type,
                " or ".join(supported_types),
            )

    @staticmethod
    def get_target_type(model_name):
        target_types_map = dict(
            environment=models.Environment,
            dataset=models.Dataset,
            notebook=models.SagemakerNotebook,
            mlstudio=models.SagemakerStudioUserProfile,
            pipeline=models.SqlPipeline,
            redshift=models.RedshiftCluster,
        )
        return [k for k, v in target_types_map.items() if v == model_name][0]
