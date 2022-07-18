import logging
import json

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
    def create_bucket_prefix(location):
        try:
            accountid = location.AWSAccountId
            aws_session = SessionHelper.remote_session(accountid=accountid)
            s3cli = aws_session.client('s3')
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
            aws_session = SessionHelper.remote_session(accountid=account_id)
            s3cli = aws_session.client('s3')
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
            aws_session = SessionHelper.remote_session(accountid=account_id)
            s3cli = aws_session.client('s3')
            response = s3cli.get_bucket_policy(Bucket=bucket_name, ExpectedBucketOwner=account_id)
            return response['Policy']
        except Exception as e:
            log.warning(
                f'Failed to get bucket policy of {bucket_name} : {e}'
            )
            return None

    @staticmethod
    def get_bucket_access_point(account_id: str, access_point_name: str):
        try:
            aws_session = SessionHelper.remote_session(accountid=account_id)
            s3control = aws_session.client('s3control')
            s3control.get_access_point(
                AccountId=account_id,
                Name=access_point_name,
            )
            return True
        except Exception as e:
            log.info(
                f'Failed to get S3 bucket access point {access_point_name} on {account_id} : {e}'
            )
            return False

    @staticmethod
    def create_bucket_access_point(account_id: str, bucket_name: str, access_point_name: str):
        try:
            aws_session = SessionHelper.remote_session(accountid=account_id)
            s3control = aws_session.client('s3control')
            access_point = s3control.create_access_point(
                AccountId=account_id,
                Name=access_point_name,
                Bucket=bucket_name,
            )
            return access_point
        except Exception as e:
            log.error(
                f'S3 bucket access point creation failed for location {bucket_name} : {e}'
            )
            raise e

    @staticmethod
    def get_access_point_policy(account_id: str, access_point_name: str):
        try:
            aws_session = SessionHelper.remote_session(accountid=account_id)
            s3control = aws_session.client('s3control')
            response = s3control.get_access_point_policy(
                AccountId=account_id,
                Name=access_point_name,
            )
            return response['Policy']
        except Exception as e:
            log.info(
                f'Failed to get policy of access point {access_point_name} on {account_id} : {e}'
            )
            return None

    @staticmethod
    def attach_access_point_policy(account_id: str, access_point_name: str, policy: str):
        try:
            aws_session = SessionHelper.remote_session(accountid=account_id)
            s3control = aws_session.client('s3control')
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
