import abc
import logging

from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.modules.dataset_sharing.db.share_object_models import ShareObject
from dataall.modules.datasets_base.db.dataset_models import Dataset


logger = logging.getLogger(__name__)


class ShareManagerUtils:
    def __init__(
            self,
            session,
            dataset: Dataset,
            share: ShareObject,
            source_environment: Environment,
            target_environment: Environment,
            source_env_group: EnvironmentGroup,
            env_group: EnvironmentGroup,
    ):
        self.target_requester_IAMRoleName = share.principalIAMRoleName
        self.session = session
        self.dataset = dataset
        self.share = share
        self.source_environment = source_environment
        self.target_environment = target_environment
        self.source_env_group = source_env_group
        self.env_group = env_group

    def add_missing_resources_to_policy_statement(
            self,
            resource_type,
            target_resources,
            existing_policy_statement,
            iam_role_policy_name
    ):
        """
        Checks if the resources are in the existing policy. Otherwise, it will add it.
        :param resource_type: str
        :param target_resources: list
        :param existing_policy_statement: dict
        :param iam_role_policy_name: str
        :return
        """
        for target_resource in target_resources:
            if not self.check_resource_in_policy_statement([target_resource], existing_policy_statement):
                logger.info(
                    f'{iam_role_policy_name} exists for IAM role {self.target_requester_IAMRoleName}, '
                    f'but {resource_type} is not included, updating...'
                )
                existing_policy_statement["Resource"].extend([target_resource])
        else:
            logger.info(
                f'{iam_role_policy_name} exists for IAM role {self.target_requester_IAMRoleName} '
                f'and {resource_type} is included, skipping...'
            )

    def check_resource_in_policy_statement(
            self,
            target_resources: list,
            existing_policy_statement: dict,
    ):
        """
        Checks if the resources are in the existing policy
        :param target_resources: list
        :param existing_policy_statement: dict
        :return True if all target_resources in the existing policy else False
        """
        for target_resource in target_resources:
            if target_resource not in existing_policy_statement["Resource"]:
                return False
        return True
                
    @staticmethod
    def remove_resource_from_statement(policy_statement, target_resources):
        for target_resource in target_resources:
            if target_resource in policy_statement["Resource"]:
                policy_statement["Resource"].remove(target_resource)
