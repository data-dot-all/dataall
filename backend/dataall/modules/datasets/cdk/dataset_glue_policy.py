from dataall.cdkproxy.stacks.policies.service_policy import ServicePolicy
from aws_cdk import aws_iam as iam

from dataall.modules.datasets.services.dataset_permissions import CREATE_DATASET


class DatasetGlueServicePolicy(ServicePolicy):
    def get_statements(self, group_permissions, **kwargs):
        if CREATE_DATASET not in group_permissions:
            return []

        statements = [
            iam.PolicyStatement(
                actions=[
                    'glue:Get*',
                    'glue:List*',
                    'glue:BatchGet*',
                    'glue:CreateClassifier',
                    'glue:CreateScript',
                    'glue:CreateSecurityConfiguration',
                    'glue:DeleteClassifier',
                    'glue:DeleteResourcePolicy',
                    'glue:DeleteSecurityConfiguration',
                    'glue:ResetJobBookmark',
                    'glue:PutDataCatalogEncryptionSettings',
                    'glue:PutResourcePolicy',
                    'glue:StartCrawlerSchedule',
                    'glue:StartJobRun',
                    'glue:StopCrawlerSchedule',
                    'glue:TagResource',
                    'glue:UntagResource',
                    'glue:UpdateClassifier',
                    'glue:UpdateCrawlerSchedule',
                    'glue:BatchStopJobRun',
                    'glue:SearchTables',
                ],
                resources=[
                    '*',
                ],
            ),
            iam.PolicyStatement(
                actions=[
                    'glue:CreateConnection',
                    'glue:CreateDatabase',
                    'glue:CreatePartition',
                    'glue:CreateTable',
                    'glue:CreateUserDefinedFunction',
                    'glue:DeleteConnection',
                    'glue:DeleteDatabase',
                    'glue:DeleteTable',
                    'glue:DeleteTableVersion',
                    'glue:DeleteUserDefinedFunction',
                    'glue:UpdateConnection',
                    'glue:UpdateDatabase',
                    'glue:UpdatePartition',
                    'glue:UpdateTable',
                    'glue:UpdateUserDefinedFunction',
                    'glue:BatchCreatePartition',
                    'glue:BatchDeleteConnection',
                    'glue:BatchDeletePartition',
                    'glue:BatchDeleteTable',
                    'glue:BatchDeleteTableVersion',
                    'glue:BatchGetPartition',
                ],
                resources=[
                    f'arn:aws:glue:{self.region}:{self.account}:userDefinedFunction/{self.resource_prefix}*/*',
                    f'arn:aws:glue:{self.region}:{self.account}:database/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:catalog',
                    f'arn:aws:glue:{self.region}:{self.account}:table/{self.resource_prefix}*/*',
                    f'arn:aws:glue:{self.region}:{self.account}:connection/{self.resource_prefix}*',
                ],
            ),
            iam.PolicyStatement(
                actions=[
                    'glue:CreateDevEndpoint',
                    'glue:CreateCrawler',
                    'glue:CreateJob',
                    'glue:CreateTrigger',
                ],
                resources=[
                    f'arn:aws:glue:{self.region}:{self.account}:crawler/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:job/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:devEndpoint/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:catalog',
                    f'arn:aws:glue:{self.region}:{self.account}:trigger/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:table/{self.resource_prefix}*/*',
                ],
                conditions={
                    'StringEquals': {f'aws:RequestTag/{self.tag_key}': [self.tag_value]}
                },
            ),
            iam.PolicyStatement(
                actions=[
                    'glue:DeleteDevEndpoint',
                    'glue:DeleteCrawler',
                    'glue:DeleteJob',
                    'glue:DeleteTrigger',
                    'glue:StartCrawler',
                    'glue:StartTrigger',
                    'glue:StopCrawler',
                    'glue:StopTrigger',
                    'glue:UpdateCrawler',
                    'glue:UpdateDevEndpoint',
                    'glue:UpdateJob',
                    'glue:UpdateTrigger',
                ],
                resources=[
                    f'arn:aws:glue:{self.region}:{self.account}:crawler/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:job/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:devEndpoint/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:catalog',
                    f'arn:aws:glue:{self.region}:{self.account}:trigger/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:table/{self.resource_prefix}*/*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:resourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
        ]
        return statements
