PIPELINE_STACK_CDK_NAG_EXCLUSIONS = [
    {
        'id': 'AwsSolutions-RDS6',
        'reason': 'IAM Database Auth is not available on Aurora Serverless',
    },
    {
        'id': 'AwsSolutions-RDS11',
        'reason': 'Port change impacts multiple components and requires costly refactoring. Postponed for now',
    },
    {
        'id': 'AwsSolutions-IAM5',
        'reason': 'Least privilege is ensured through resource prefixes scoping',
    },
    {'id': 'AwsSolutions-S1', 'reason': 'Recursive s3 access logs problem'},
    {
        'id': 'AwsSolutions-CB4',
        'reason': 'CodeBuild projects encryption is not supported on CDK Pipelines',
    },
    {
        'id': 'AwsSolutions-KMS5',
        'reason': 'CDK pipeline KMS key properties are not accessible from cdk',
    },
    {
        'id': 'AwsSolutions-S10',
        'reason': 'CDK pipelines artifact bucket is not accessible from cdk',
    },
    {
        'id': 'AwsSolutions-CB3',
        'reason': 'Access to docker daemon is required to build docker images',
    },
    {
        'id': 'AwsSolutions-SMG4',
        'reason': 'Database is used for test purposes',
    },
]

BACKEND_STACK_CDK_NAG_EXCLUSIONS = [
    {
        'id': 'AwsSolutions-RDS6',
        'reason': 'IAM Database Auth is not available on Aurora Serverless',
    },
    {
        'id': 'AwsSolutions-RDS11',
        'reason': 'Port change impacts multiple components and requires costly refactoring. Postponed for now',
    },
    {
        'id': 'AwsSolutions-SMG4',
        'reason': 'Rotating IAM external ID will impact the onboarded environments hence disabled',
    },
    {
        'id': 'AwsSolutions-IAM5',
        'reason': 'Least privilege is ensured through resource prefixes scoping',
    },
    {
        'id': 'AwsSolutions-IAM4',
        'reason': 'Managed policies are used by CDK custom resources',
    },
    {
        'id': 'AwsSolutions-SQS2',
        'reason': 'SQS is only used for lambda functions dead letter queues with no encryption',
    },
    {
        'id': 'AwsSolutions-SQS3',
        'reason': 'SQS is only used for lambda functions dead letter queues.',
    },
    {'id': 'AwsSolutions-S1', 'reason': 'Recursive s3 access logs problem'},
    {
        'id': 'AwsSolutions-CFR5',
        'reason': 'Does not occur if the customer brings his own Route53 domain and hosted zone id',
    },
    {
        'id': 'AwsSolutions-ECS7',
        'reason': 'All ECS tasks have logging enabled is this a false positive ?',
    },
    {
        'id': 'AwsSolutions-COG2',
        'reason': 'The Cognito user pool does not require MFA which is not needed as we use federation',
    },
    {
        'id': 'AwsSolutions-COG4',
        'reason': '/{proxy+}/OPTIONS method does not require authorizer as it is used for preflight cors requests only',
    },
    {
        'id': 'AwsSolutions-COG7',
        'reason': 'The Cognito identity pool allows for unauthenticated logins required for cloudwatch RUM',
    },
    {
        'id': 'AwsSolutions-CB4',
        'reason': 'CodeBuild projects are not encrypted; Not very relevant '
        'and not clear how to do it with CDKPipelines construct',
    },
    {'id': 'AwsSolutions-OS3', 'reason': 'Could not provide a fix'},
    {'id': 'AwsSolutions-OS5', 'reason': 'Could not provide a fix'},
    {'id': 'AwsSolutions-KMS5', 'reason': 'Could not provide a fix'},
    {
        'id': 'AwsSolutions-APIG4',
        'reason': 'OPTIONS method for CORS preflight request does not require an authorizer',
    },
    {
        'id': 'AwsSolutions-OS4',
        'reason': 'Excluded only when dev sizing is enabled to lower dev env costs',
    },
    {
        'id': 'AwsSolutions-ECS2',
        'reason': 'Technical data is added to environment variables',
    },
]

CLOUDFRONT_STACK_CDK_NAG_EXCLUSIONS = [
    {'id': 'AwsSolutions-S1', 'reason': 'Recursive s3 access logs problem'},
    {
        'id': 'AwsSolutions-CFR5',
        'reason': 'Does not occur if the customer brings his own Route53 domain and hosted zone id',
    },
    {
        'id': 'AwsSolutions-CFR1',
        'reason': 'CloudFront distributions Geo restriction is not required',
    },
    {
        'id': 'AwsSolutions-IAM5',
        'reason': 'Least privilege is ensured through resource prefixes scoping',
    },
    {
        'id': 'AwsSolutions-IAM4',
        'reason': 'Managed policies are used by CDK custom resources',
    },
]

ALBFRONT_STACK_CDK_NAG_EXCLUSIONS = [
    {'id': 'AwsSolutions-S1', 'reason': 'Recursive s3 access logs problem'},
    {
        'id': 'AwsSolutions-ELB2',
        'reason': 'Access logs are enable but error is persisting. could not provide a fix',
    },
    {
        'id': 'AwsSolutions-IAM5',
        'reason': 'Least privilege is ensured through resource prefixes scoping',
    },
    {
        'id': 'AwsSolutions-IAM4',
        'reason': 'Managed policies are used by CDK custom resources',
    },
    {
        'id': 'AwsSolutions-ECS2',
        'reason': 'Technical data is added to environment variables',
    },
]
