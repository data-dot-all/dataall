from typing import List
import logging
import json
from dataall.base.aws.iam import IAM

logger = logging.getLogger(__name__)


class ManagedPolicy(object):
    def __init__(
            self,
            role_name,
            account,
            environmentUri,
            resource_prefix
    ):
        self.role_name = role_name
        self.account = account
        self.environmentUri = environmentUri
        self.resource_prefix = resource_prefix

    def create_all_policies(self, managed) -> bool:
        """
        Manager that registers and calls all policies created by data.all modules and that
        need to be created for consumption roles and team roles
        """

        policies = ManagedPolicy.__subclasses__()
        logger.info(f'Found {len(policies)} subclasses of ManagedPolicy')
        for policy in policies:
            empty_policy = policy.generate_empty_policy(self)
            policy_name = policy.generate_policy_name(self)

            IAM.create_managed_policy(
                account_id=self.account,
                policy_name=policy_name,
                policy=json.dumps(empty_policy)
            )

            if managed:
                IAM.attach_role_policy(
                    account_id=self.account,
                    role_name=self.role_name,
                    policy_arn=policy_name
                )
        return True

    def delete_all_policies(self) -> bool:
        """
        Manager that registers and calls all policies created by data.all modules and that
        need to be deleted for consumption roles and team roles
        """

        policies = ManagedPolicy.__subclasses__()
        logger.info(f'Found {len(policies)} subclasses of ManagedPolicy')
        for policy in policies:
            policy_name = policy.generate_policy_name(self)

            IAM.detach_policy_from_role(
                account_id=self.account,
                role_name=self.role_name,
                policy_name=policy_name
            )

            IAM.delete_managed_policy_by_name(
                account_id=self.account,
                policy_name=policy_name
            )
        return True

    def list_all_policies(self) -> List[str]:
        """
        Manager that registers and calls all policies created by data.all modules and that
        need to be listed for consumption roles and team roles
        """
        all_policies = []
        policies = ManagedPolicy.__subclasses__()
        logger.info(f'Found {len(policies)} subclasses of ManagedPolicy')
        for policy in policies:
            all_policies.append(policy.generate_policy_name(self))
        return all_policies

    def check_all_policies_attached(self) -> List[bool]:
        """
        Manager that registers and calls all policies created by data.all modules and that
        need to be checked if attached for consumption roles and team roles
        """
        all_policies = []
        policies = ManagedPolicy.__subclasses__()
        logger.info(f'Found {len(policies)} subclasses of ManagedPolicy')
        for policy in policies:
            policy_name = policy.generate_policy_name(self)
            all_policies.append(IAM.is_policy_attached(self.account, policy_name, self.role_name))
        return all_policies

    def generate_policy_name(self) -> str:
        """
        Returns string and needs to be implemented in the ManagedPolicies inherited classes
        """
        return NotImplementedError

    def generate_empty_policy(self) -> dict:
        """
        Returns dict and needs to be implemented in the ManagedPolicies inherited classes
        """
        return NotImplementedError
