from typing import List
import logging
import json
from abc import ABC, abstractmethod
from dataall.base.aws.iam import IAM

logger = logging.getLogger(__name__)


class ManagedPolicy(ABC):
    """
    Abstract class for any IAM Managed policy that needs to be atached to data.all team IAM roles and consumption roles
    """

    @abstractmethod
    def __init__(self, role_name, account, environmentUri, resource_prefix):
        self.role_name = role_name
        self.account = account
        self.environmentUri = environmentUri
        self.resource_prefix = resource_prefix

    @property
    @abstractmethod
    def policy_type(self):
        """
        Returns string and needs to be implemented in the ManagedPolicies inherited classes
        """
        raise NotImplementedError

    @abstractmethod
    def generate_policy_name(self) -> str:
        """
        Returns string and needs to be implemented in the ManagedPolicies inherited classes
        """
        raise NotImplementedError

    @abstractmethod
    def generate_empty_policy(self) -> dict:
        """
        Returns dict and needs to be implemented in the ManagedPolicies inherited classes
        """
        raise NotImplementedError

    def check_if_policy_exists(self) -> bool:
        policy_name = self.generate_policy_name()
        share_policy = IAM.get_managed_policy_by_name(self.account, policy_name)
        return share_policy is not None

    def check_if_policy_attached(self):
        policy_name = self.generate_policy_name()
        return IAM.is_policy_attached(self.account, policy_name, self.role_name)

    def attach_policy(self):
        policy_arn = f'arn:aws:iam::{self.account}:policy/{self.generate_policy_name()}'
        try:
            IAM.attach_role_policy(self.account, self.role_name, policy_arn)
        except Exception as e:
            raise Exception(f"Required customer managed policy {policy_arn} can't be attached: {e}")


class PolicyManager(object):
    def __init__(
        self,
        role_name,
        account,
        environmentUri,
        resource_prefix,
    ):
        self.role_name = role_name
        self.account = account
        self.environmentUri = environmentUri
        self.resource_prefix = resource_prefix
        self.ManagedPolicies = ManagedPolicy.__subclasses__()
        logger.info(f'Found {len(self.ManagedPolicies)} subclasses of ManagedPolicy')
        self.initializedPolicies = [self._initialize_policy(policy) for policy in self.ManagedPolicies]

    def _initialize_policy(self, managedPolicy):
        return managedPolicy(
            role_name=self.role_name,
            account=self.account,
            environmentUri=self.environmentUri,
            resource_prefix=self.resource_prefix,
        )

    def create_all_policies(self, managed) -> bool:
        """
        Manager that registers and calls all policies created by data.all modules and that
        need to be created for consumption roles and team roles
        """
        try:
            for Policy in self.initializedPolicies:
                empty_policy = Policy.generate_empty_policy()
                policy_name = Policy.generate_policy_name()
                logger.info(f'Creating policy {policy_name}')

                IAM.create_managed_policy(
                    account_id=self.account, policy_name=policy_name, policy=json.dumps(empty_policy)
                )

                if managed:
                    IAM.attach_role_policy(
                        account_id=self.account,
                        role_name=self.role_name,
                        policy_arn=f'arn:aws:iam::{self.account}:policy/{policy_name}',
                    )
        except Exception as e:
            raise e
        return True

    def delete_all_policies(self) -> bool:
        """
        Manager that registers and calls all policies created by data.all modules and that
        need to be deleted for consumption roles and team roles
        """
        try:
            for Policy in self.initializedPolicies:
                policy_name = Policy.generate_policy_name()
                logger.info(f'Deleting policy {policy_name}')
                if Policy.check_if_policy_attached():
                    IAM.detach_policy_from_role(
                        account_id=self.account, role_name=self.role_name, policy_name=policy_name
                    )
                if Policy.check_if_policy_exists():
                    IAM.delete_managed_policy_non_default_versions(account_id=self.account, policy_name=policy_name)
                    IAM.delete_managed_policy_by_name(account_id=self.account, policy_name=policy_name)
        except Exception as e:
            raise e
        return True

    def get_all_policies(self) -> List[dict]:
        """
        Manager that registers and calls all policies created by data.all modules and that
        need to be listed for consumption roles and team roles
        """
        all_policies = []
        for Policy in self.initializedPolicies:
            policy_dict = {
                'policy_name': Policy.generate_policy_name(),
                'policy_type': Policy.policy_type,
                'exists': Policy.check_if_policy_exists(),
                'attached': Policy.check_if_policy_attached(),
            }
            all_policies.append(policy_dict)
        logger.info(f'All policies currently added to role {str(all_policies)}')
        return all_policies
