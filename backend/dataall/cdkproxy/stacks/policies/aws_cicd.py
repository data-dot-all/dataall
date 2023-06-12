from .service_policy import ServicePolicy
from aws_cdk import aws_iam as iam


class AwsCICD(ServicePolicy):
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid="GenericCodeCommit",
                actions=[
                    'codecommit:ListRepositoriesForApprovalRuleTemplate',
                    'codecommit:CreateApprovalRuleTemplate',
                    'codecommit:UpdateApprovalRuleTemplateName',
                    'codecommit:GetApprovalRuleTemplate',
                    'codecommit:ListApprovalRuleTemplates',
                    'codecommit:DeleteApprovalRuleTemplate',
                    'codecommit:ListRepositories',
                    'codecommit:UpdateApprovalRuleTemplateContent',
                    'codecommit:UpdateApprovalRuleTemplateDescription',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid="AllCodecommitTeamRepo",
                actions=['codecommit:*'],
                resources=[
                    f'arn:aws:codecommit:{self.region}:{self.account}:{self.resource_prefix}*'
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value],
                    },
                },
            ),
            iam.PolicyStatement(
                sid="GenericCodePipeline",
                actions=[
                    'codepipeline:PutThirdPartyJobSuccessResult',
                    'codepipeline:PutThirdPartyJobFailureResult',
                    'codepipeline:PollForThirdPartyJobs',
                    'codepipeline:PutJobFailureResult',
                    'codepipeline:PutJobSuccessResult',
                    'codepipeline:ListPipelines',
                    'codepipeline:AcknowledgeJob',
                    'codepipeline:AcknowledgeThirdPartyJob',
                    'codepipeline:GetThirdPartyJobDetails',
                    'codepipeline:GetJobDetails',
                    'codepipeline:GetActionType',
                    'codepipeline:ListActionTypes',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid="AllCodepipelineTeamRepo",
                actions=['codepipeline:*'],
                resources=[
                    f'arn:aws:codepipeline:{self.region}:{self.account}:{self.resource_prefix}*/*/*',
                    f'arn:aws:codepipeline:{self.region}:{self.account}:actiontype:/*/*/*',
                    f'arn:aws:codepipeline:{self.region}:{self.account}:{self.resource_prefix}*',
                    f'arn:aws:codepipeline:{self.region}:{self.account}:{self.resource_prefix}*/*',
                    f'arn:aws:codepipeline:{self.region}:{self.account}:webhook:{self.resource_prefix}',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="AllCodebuildTeamRepo",
                actions=['codebuild:*'],
                resources=[
                    f'arn:aws:codebuild:{self.region}:{self.account}:project/{self.resource_prefix}*',
                    f'arn:aws:codebuild:{self.region}:{self.account}:report-group/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="GenericCodeBuild",
                actions=[
                    'codebuild:ListCuratedEnvironmentImages',
                    'codebuild:ListReportGroups',
                    'codebuild:ListSourceCredentials',
                    'codebuild:ListRepositories',
                    'codebuild:ListSharedProjects',
                    'codebuild:ListBuildBatches',
                    'codebuild:ListSharedReportGroups',
                    'codebuild:ImportSourceCredentials',
                    'codebuild:ListReports',
                    'codebuild:ListBuilds',
                    'codebuild:DeleteOAuthToken',
                    'codebuild:ListProjects',
                    'codebuild:DeleteSourceCredentials',
                    'codebuild:PersistOAuthToken',
                    'codebuild:ListConnectedOAuthAccounts',
                ],
                resources=['*'],
            ),
        ]
        return statements
