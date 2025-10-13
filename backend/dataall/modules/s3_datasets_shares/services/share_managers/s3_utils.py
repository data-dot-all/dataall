from enum import Enum, auto
from typing import List

from dataall.modules.s3_datasets_shares.aws.kms_client import (
    DATAALL_BUCKET_KMS_DECRYPT_SID,
    DATAALL_BUCKET_KMS_ENCRYPT_SID,
    DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID,
    DATAALL_ACCESS_POINT_KMS_DECRYPT_SID,
    DATAALL_ACCESS_POINT_KMS_ENCRYPT_SID,
)
from dataall.modules.s3_datasets_shares.aws.s3_client import (
    DATAALL_READ_ONLY_SID,
    DATAALL_WRITE_ONLY_SID,
    DATAALL_MODIFY_ONLY_SID,
)
from dataall.modules.shares_base.services.shares_enums import ShareObjectDataPermission

SID_TO_ACTIONS = {
    DATAALL_READ_ONLY_SID: ['s3:List*', 's3:GetObject'],
    DATAALL_WRITE_ONLY_SID: ['s3:PutObject'],
    DATAALL_MODIFY_ONLY_SID: ['s3:DeleteObject'],
    DATAALL_BUCKET_KMS_DECRYPT_SID: ['kms:Decrypt'],
    DATAALL_BUCKET_KMS_ENCRYPT_SID: ['kms:Encrypt', 'kms:ReEncrypt*', 'kms:GenerateDataKey*'],
    DATAALL_ACCESS_POINT_KMS_DECRYPT_SID: ['kms:Decrypt'],
    DATAALL_ACCESS_POINT_KMS_ENCRYPT_SID: ['kms:Encrypt', 'kms:ReEncrypt*', 'kms:GenerateDataKey*'],
    DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID: [
        'kms:Decrypt',
        'kms:Encrypt',
        'kms:GenerateDataKey*',
        'kms:PutKeyPolicy',
        'kms:GetKeyPolicy',
        'kms:ReEncrypt*',
        'kms:TagResource',
        'kms:UntagResource',
        'kms:DescribeKey',
        'kms:List*',
    ],
}


class SidType(Enum):
    BucketPolicy = auto()
    KmsBucketPolicy = auto()
    KmsAccessPointPolicy = auto()


PERM_TO_SID = {
    ShareObjectDataPermission.Read.value: {
        SidType.BucketPolicy: DATAALL_READ_ONLY_SID,
        SidType.KmsBucketPolicy: DATAALL_BUCKET_KMS_DECRYPT_SID,
        SidType.KmsAccessPointPolicy: DATAALL_ACCESS_POINT_KMS_DECRYPT_SID,
    },
    ShareObjectDataPermission.Write.value: {
        SidType.BucketPolicy: DATAALL_WRITE_ONLY_SID,
        SidType.KmsBucketPolicy: DATAALL_BUCKET_KMS_ENCRYPT_SID,
        SidType.KmsAccessPointPolicy: DATAALL_ACCESS_POINT_KMS_ENCRYPT_SID,
    },
    ShareObjectDataPermission.Modify.value: {
        SidType.BucketPolicy: DATAALL_MODIFY_ONLY_SID,
        SidType.KmsBucketPolicy: DATAALL_BUCKET_KMS_ENCRYPT_SID,
        SidType.KmsAccessPointPolicy: DATAALL_ACCESS_POINT_KMS_ENCRYPT_SID,
    },
}


def get_principal_list(statement):
    principal_list = statement['Principal']['AWS']
    if isinstance(principal_list, str):
        principal_list = [principal_list]
    return principal_list


def add_target_arn_to_statement_principal(statement, target_requester_arn):
    principal_list = get_principal_list(statement)
    if f'{target_requester_arn}' not in principal_list:
        principal_list.append(f'{target_requester_arn}')
    statement['Principal']['AWS'] = principal_list
    return statement


def generate_policy_statement(target_sid, target_requester_arns, target_resources):
    return {
        'Sid': target_sid,
        'Effect': 'Allow',
        'Principal': {'AWS': target_requester_arns},
        'Action': SID_TO_ACTIONS[target_sid],
        'Resource': target_resources,
    }


def perms_to_sids(permissions: List[str], sid_type: SidType) -> List[str]:
    """
    :return: unique SIDs
    """
    return list(dict.fromkeys([PERM_TO_SID[perm][sid_type] for perm in permissions]))


def perms_to_actions(permissions: List[str], sid_type: SidType) -> List[str]:
    actions = list()
    for sid in perms_to_sids(permissions, sid_type):
        actions.extend(SID_TO_ACTIONS[sid])
    return list(dict.fromkeys(actions))
