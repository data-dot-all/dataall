"""
**Warning:** This file is symlinked and reused in CDK deploy/stacks/cdk_asset_trail.py
"""

from aws_cdk import Stack
from aws_cdk.aws_cloudtrail import Trail, S3EventSelector, ReadWriteType
from aws_cdk.aws_s3 import Bucket, IBucket


def setup_cdk_asset_trail(stack: Stack, server_access_logs_bucket: IBucket) -> Trail:
    """
    Sets up CloudTrail logging for CDK asset bucket.

    Args:
        stack (Stack): The CDK stack instance
        server_access_logs_bucket (IBucket): S3 bucket to store CloudTrail logs

    Returns:
        Trail: The configured CloudTrail instance
    """
    target_bucket_name = f'cdk-{stack.synthesizer.bootstrap_qualifier}-assets-{stack.account}-{stack.region}'
    trail = Trail(
        scope=stack,
        id='S3CloudTrail',
        bucket=server_access_logs_bucket,
    )

    trail.add_s3_event_selector(
        [
            S3EventSelector(
                bucket=Bucket.from_bucket_name(
                    scope=stack,
                    id='CDKToolkitAssetsBucket',
                    bucket_name=target_bucket_name,
                ),
            ),
        ],
        include_management_events=True,
        read_write_type=ReadWriteType.ALL,
    )

    return trail
