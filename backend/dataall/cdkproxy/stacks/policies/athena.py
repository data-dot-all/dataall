from .service_policy import ServicePolicy
from aws_cdk import aws_iam as iam


class Athena(ServicePolicy):

    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid="ListAthena",
                actions=[
                    "athena:ListWorkGroups",
                    "athena:ListTagsForResource",
                    "athena:GetWorkgroup"
                ],
                effect=iam.Effect.ALLOW,
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid="AthenaWorkgroup",
                actions=[
                    "athena:GetWorkGroup",
                    "athena:BatchGetQueryExecution",
                    "athena:GetQueryExecution",
                    "athena:ListQueryExecutions",
                    "athena:StartQueryExecution",
                    "athena:StopQueryExecution",
                    "athena:GetQueryResults",
                    "athena:GetQueryResultsStream",
                    "athena:CreateNamedQuery",
                    "athena:GetNamedQuery",
                    "athena:BatchGetNamedQuery",
                    "athena:ListNamedQueries",
                    "athena:DeleteNamedQuery",
                    "athena:CreatePreparedStatement",
                    "athena:GetPreparedStatement",
                    "athena:ListPreparedStatements",
                    "athena:UpdatePreparedStatement",
                    "athena:DeletePreparedStatement"
                ],
                resources=[f'arn:aws:athena:{self.region}:{self.account}:workgroup/{self.team.environmentAthenaWorkGroup}'],
            ),
            iam.PolicyStatement(
                sid="ListBucketAthena",
                actions=[
                    "s3:ListBucket",
                ],
                effect=iam.Effect.ALLOW,
                resources=[f'arn:aws:s3:::{self.environment.EnvironmentDefaultBucketName}'],
                conditions={"StringEquals": {"s3:prefix": ["", "athenaqueries/", f"athenaqueries/{self.team.environmentIAMRoleName}/"], "s3:delimiter": ["/"]}}
            ),
            iam.PolicyStatement(
                sid="ReadWriteEnvironmentBucketAthenaQueries",
                actions=[
                    "s3:PutObject",
                    "s3:PutObjectAcl",
                    "s3:GetObject",
                    "s3:GetObjectAcl",
                    "s3:GetObjectVersion",
                    "s3:DeleteObject"
                ],
                resources=[
                    f'arn:aws:s3:::{self.environment.EnvironmentDefaultBucketName}/athenaqueries/{self.team.environmentIAMRoleName}/*'],
                effect=iam.Effect.ALLOW,
            ),
        ]
        return statements
