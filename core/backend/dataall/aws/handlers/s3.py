import logging

from ... import db
from ...db import models
from .service_handlers import Worker
from .sts import SessionHelper

log = logging.getLogger(__name__)


class S3:
    @staticmethod
    @Worker.handler(path='s3.prefix.create')
    def create_dataset_location(engine, task: models.Task):
        with engine.scoped_session() as session:
            location = db.api.DatasetStorageLocation.get_location_by_uri(
                session, task.targetUri
            )
            S3.create_bucket_prefix(location)
            return location

    @staticmethod
    def client(account_id: str, client_type: str):
        session = SessionHelper.remote_session(accountid=account_id)
        return session.client(client_type)

    @staticmethod
    def create_bucket_prefix(location):
        try:
            accountid = location.AWSAccountId
            s3cli = S3.client(account_id=accountid, client_type='s3')
            response = s3cli.put_object(
                Bucket=location.S3BucketName, Body='', Key=location.S3Prefix + '/'
            )
            log.info(
                'Creating S3 Prefix `{}`({}) on AWS #{}'.format(
                    location.S3BucketName, accountid, response
                )
            )
            location.locationCreated = True
        except Exception as e:
            log.error(
                f'Dataset storage location creation failed on S3 for dataset location {location.locationUri} : {e}'
            )
            raise e

    @staticmethod
    def create_bucket_policy(account_id: str, bucket_name: str, policy: str):
        try:
            s3cli = S3.client(account_id=account_id, client_type='s3')
            s3cli.put_bucket_policy(
                Bucket=bucket_name,
                Policy=policy,
                ConfirmRemoveSelfBucketAccess=False,
                ExpectedBucketOwner=account_id,
            )
            log.info(
                f'Created bucket policy of {bucket_name} on {account_id} successfully'
            )
        except Exception as e:
            log.error(
                f'Bucket policy created failed on bucket {bucket_name} of {account_id} : {e}'
            )
            raise e

    @staticmethod
    def get_bucket_policy(account_id: str, bucket_name: str):
        try:
            s3cli = S3.client(account_id=account_id, client_type='s3')
            response = s3cli.get_bucket_policy(Bucket=bucket_name, ExpectedBucketOwner=account_id)
        except Exception as e:
            log.warning(
                f'Failed to get bucket policy of {bucket_name} : {e}'
            )
            return None
        else:
            return response['Policy']

    @staticmethod
    def get_bucket_access_point_arn(account_id: str, access_point_name: str):
        try:
            s3control = S3.client(account_id, 's3control')
            access_point = s3control.get_access_point(
                AccountId=account_id,
                Name=access_point_name,
            )
        except Exception as e:
            log.info(
                f'Failed to get S3 bucket access point {access_point_name} on {account_id} : {e}'
            )
            return None
        else:
            return access_point["AccessPointArn"]

    @staticmethod
    def create_bucket_access_point(account_id: str, bucket_name: str, access_point_name: str):
        try:
            s3control = S3.client(account_id, 's3control')
            access_point = s3control.create_access_point(
                AccountId=account_id,
                Name=access_point_name,
                Bucket=bucket_name,
            )
        except Exception as e:
            log.error(
                f'S3 bucket access point creation failed for location {bucket_name} : {e}'
            )
            raise e
        else:
            return access_point["AccessPointArn"]

    @staticmethod
    def delete_bucket_access_point(account_id: str, access_point_name: str):
        try:
            s3control = S3.client(account_id, 's3control')
            s3control.delete_access_point(
                AccountId=account_id,
                Name=access_point_name,
            )
        except Exception as e:
            log.error(
                f'Failed to delete S3 bucket access point {access_point_name}/{account_id} : {e}'
            )
            raise e

    @staticmethod
    def get_access_point_policy(account_id: str, access_point_name: str):
        try:
            s3control = S3.client(account_id, 's3control')
            response = s3control.get_access_point_policy(
                AccountId=account_id,
                Name=access_point_name,
            )
        except Exception as e:
            log.info(
                f'Failed to get policy of access point {access_point_name} on {account_id} : {e}'
            )
            return None
        else:
            return response['Policy']

    @staticmethod
    def attach_access_point_policy(account_id: str, access_point_name: str, policy: str):
        try:
            s3control = S3.client(account_id, 's3control')
            s3control.put_access_point_policy(
                AccountId=account_id,
                Name=access_point_name,
                Policy=policy
            )
        except Exception as e:
            log.error(
                f'S3 bucket access point policy creation failed : {e}'
            )
            raise e

    @staticmethod
    def generate_access_point_policy_template(
        principal_id: str,
        access_point_arn: str,
        s3_prefix: str,
    ):
        policy = {
            'Version': '2012-10-17',
            "Statement": [
                {
                    "Sid": f"{principal_id}0",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "*"
                    },
                    "Action": "s3:ListBucket",
                    "Resource": f"{access_point_arn}",
                    "Condition": {
                        "StringLike": {
                            "s3:prefix": [f"{s3_prefix}/*"],
                            "aws:userId": [f"{principal_id}:*"]
                        }
                    }
                },
                {
                    "Sid": f"{principal_id}1",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "*"
                    },
                    "Action": "s3:GetObject",
                    "Resource": [f"{access_point_arn}/object/{s3_prefix}/*"],
                    "Condition": {
                        "StringLike": {
                            "aws:userId": [f"{principal_id}:*"]
                        }
                    }
                }
            ]
        }
        return policy
