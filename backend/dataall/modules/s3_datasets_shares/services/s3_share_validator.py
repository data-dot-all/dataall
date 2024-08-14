from dataall.base.db.exceptions import UnauthorizedOperation
from dataall.base.aws.iam import IAM
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.environment.db.environment_models import EnvironmentGroup, ConsumptionRole
from dataall.core.environment.services.managed_iam_policies import PolicyManager
from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.shares_base.db.share_object_models import ShareObject
from dataall.modules.shares_base.services.share_object_service import SharesCreationValidatorInterface
from dataall.modules.shares_base.services.shares_enums import (
    PrincipalType,
)
from dataall.modules.shares_base.services.share_exceptions import PrincipalRoleNotFound
from dataall.modules.shares_base.services.share_permissions import (
    APPROVE_SHARE_OBJECT,
    SUBMIT_SHARE_OBJECT,
    CREATE_SHARE_OBJECT,
)

import logging

log = logging.getLogger(__name__)


class S3ShareValidator(SharesCreationValidatorInterface):
    @staticmethod
    def validate_share_object_creation(session, dataset_uri, *args, **kwargs) -> bool:
        log.info('Verifying S3 share request input')
        principal_id = kwargs.get('principal_id')
        principal_type = kwargs.get('principal_type')
        group_uri = kwargs.get('group_uri')
        environment = kwargs.get('environment')
        attachMissingPolicies = kwargs.get('attachMissingPolicies')

        dataset: DatasetBase = DatasetBaseRepository.get_dataset_by_uri(session, dataset_uri)
        if (
            (dataset.stewards == group_uri or dataset.SamlAdminGroupName == group_uri)
            and environment.environmentUri == dataset.environmentUri
            and principal_type == PrincipalType.Group.value
        ):
            raise UnauthorizedOperation(
                action=CREATE_SHARE_OBJECT,
                message=f'Team: {group_uri} is managing the dataset {dataset.name}',
            )
        if environment.region != dataset.region:
            raise UnauthorizedOperation(
                action=CREATE_SHARE_OBJECT,
                message=f'Requester Team {group_uri} works in region {environment.region} '
                f'and the requested dataset is stored in region {dataset.region}',
            )
        S3ShareValidator._validate_iam_role_policy(
            session, environment, principal_type, principal_id, group_uri, attachMissingPolicies
        )

        return True

    @staticmethod
    def validate_share_object_submit(session, dataset, *args, **kwargs) -> bool:
        share = kwargs.get('share')
        if not S3ShareValidator._validate_iam_role(session, share):
            raise PrincipalRoleNotFound(
                action=SUBMIT_SHARE_OBJECT,
                message=f'The principal role {share.principalRoleName} is not found.',
            )
        return True

    @staticmethod
    def validate_share_object_approve(session, dataset, *args, **kwargs) -> bool:
        share = kwargs.get('share')
        if not S3ShareValidator._validate_iam_role(session, share):
            raise PrincipalRoleNotFound(
                action=APPROVE_SHARE_OBJECT,
                message=f'The principal role {share.principalRoleName} is not found.',
            )
        return True

    @staticmethod
    def validate_share_object_start(session, dataset, *args, **kwargs) -> bool:
        share = kwargs.get('share')
        if not S3ShareValidator._validate_iam_role(session, share):
            raise PrincipalRoleNotFound(
                'process approved shares',
                f'Principal role {share.principalRoleName} is not found.',
            )
        return True

    @staticmethod
    def _validate_iam_role(session, share: ShareObject) -> bool:
        log.info('Verifying principal IAM role...')
        role_name = share.principalRoleName
        env = EnvironmentService.get_environment_by_uri(session, share.environmentUri)
        principal_role = IAM.get_role_arn_by_name(account_id=env.AwsAccountId, region=env.region, role_name=role_name)
        return principal_role is not None

    @staticmethod
    def _validate_iam_role_policy(
        session, environment, principal_type: str, principal_id: str, group_uri: str, attachMissingPolicies: bool
    ):
        if principal_type == PrincipalType.ConsumptionRole.value:
            consumption_role: ConsumptionRole = EnvironmentService.get_environment_consumption_role(
                session, principal_id, environment.environmentUri
            )
            principal_role_name = consumption_role.IAMRoleName
            managed = consumption_role.dataallManaged

        else:
            env_group: EnvironmentGroup = EnvironmentService.get_environment_group(
                session, group_uri, environment.environmentUri
            )
            principal_role_name = env_group.environmentIAMRoleName
            managed = True

        share_policy_manager = PolicyManager(
            role_name=principal_role_name,
            environmentUri=environment.environmentUri,
            account=environment.AwsAccountId,
            region=environment.region,
            resource_prefix=environment.resourcePrefix,
        )
        for Policy in [
            Policy for Policy in share_policy_manager.initializedPolicies if Policy.policy_type == 'SharePolicy'
        ]:
            # Backwards compatibility
            # we check if a managed share policy exists. If False, the role was introduced to data.all before this update
            # We create the policy from the inline statements
            # In this case it could also happen that the role is the Admin of the environment
            if not Policy.check_if_policy_exists():
                Policy.create_managed_policy_from_inline_and_delete_inline()
            # End of backwards compatibility

            attached = Policy.check_if_policy_attached()
            if not attached and not managed and not attachMissingPolicies:
                raise Exception(
                    f'Required customer managed policy {Policy.generate_policy_name()} is not attached to role {principal_role_name}'
                )
            elif not attached:
                Policy.attach_policy()
