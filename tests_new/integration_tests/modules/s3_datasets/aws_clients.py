import logging
import json
import re
import os
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)


class S3Client:
    def __init__(self, session, region):
        self._client = session.client('s3', region_name=region)
        self._resource = session.resource('s3', region_name=region)
        self._region = region

    def bucket_exists(self, bucket_name):
        """
        Check if an S3 bucket exists.
        :param bucket_name: Name of the S3 bucket to check
        :return: True if the bucket exists, False otherwise
        """
        try:
            self._client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                log.error(f'Error checking if bucket {bucket_name} exists: {e}')
                raise

    def create_bucket(self, bucket_name, kms_key_arn=None):
        """
        Create an S3 bucket.
        :param bucket_name: Name of the S3 bucket to be created
        :param kms_key_arn: KMS key Arn to use for encryption if encryption_type is 'aws:kms'
        :return: None
        """
        bucket_name = re.sub('[^a-zA-Z0-9-]', '', bucket_name).lower()

        encryption_type = 'aws:kms' if kms_key_arn else 'AES256'
        encryption_config = (
            {'SSEAlgorithm': encryption_type, 'KMSMasterKeyID': kms_key_arn}
            if encryption_type == 'aws:kms'
            else {'SSEAlgorithm': encryption_type}
        )

        try:
            if self._region == 'us-east-1':
                self._client.create_bucket(ACL='private', Bucket=bucket_name)
            else:
                create_bucket_config = {'LocationConstraint': self._region}
                self._client.create_bucket(
                    ACL='private', Bucket=bucket_name, CreateBucketConfiguration=create_bucket_config
                )

            self._client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {'ApplyServerSideEncryptionByDefault': encryption_config, 'BucketKeyEnabled': True},
                    ]
                },
            )
            return bucket_name
        except ClientError as e:
            log.exception(f'Error creating S3 bucket: {e}')

    def delete_bucket(self, bucket_name):
        """
        Delete an S3 bucket.
        :param bucket_name: Name of the S3 bucket to be deleted
        :return: None
        """
        try:
            # Delete all objects in the bucket before deleting the bucket
            bucket = self._resource.Bucket(bucket_name)
            bucket_versioning = self._resource.BucketVersioning(bucket_name)
            if bucket_versioning.status == 'Enabled':
                bucket.object_versions.delete()
            else:
                bucket.objects.all().delete()
            self._client.delete_bucket(Bucket=bucket_name)
        except ClientError as e:
            log.exception(f'Error deleting S3 bucket: {e}')

    def upload_file_to_prefix(self, local_file_path, s3_path):
        """
        Upload a file from a local path to an S3 bucket with a specified prefix.

        :param local_file_path: Path to the local file to be uploaded
        :param s3_path: S3 path where the file should be uploaded, including the bucket name and prefix
        :return: None
        """
        try:
            bucket_name, prefix = s3_path.split('/', 1)
            object_key = f'{prefix}/{os.path.basename(local_file_path)}'
            self._client.upload_file(local_file_path, bucket_name, object_key)
        except ClientError as e:
            logging.error(f'Error uploading file to S3: {e}')
            raise


class KMSClient:
    def __init__(self, session, account_id, region):
        self._client = session.client('kms', region_name=region)
        self._account_id = account_id

    def get_key_id_and_alias(self, alias_name):
        """
        Get the key ID and alias name for a given alias.
        :param alias_name: The alias name to look up
        :return: A tuple containing the key ID and alias name if the alias exists, False otherwise
        """
        try:
            alias_name = alias_name.lower()
            response = self._client.describe_key(KeyId=f'alias/{alias_name}')
            key_id = response['KeyMetadata']['KeyId']
            aliases = response['KeyMetadata']['Aliases']
            for alias in aliases:
                if alias['AliasName'] == f'alias/{alias_name}':
                    return key_id, alias['AliasName']
        except ClientError as e:
            if e.response['Error']['Code'] == 'NotFoundException':
                return False, False
            else:
                log.exception(f'Error getting key ID and alias for {alias_name}: {e}')

    def create_key_with_alias(self, alias_name):
        try:
            response = self._client.create_key()
            key_id = response['KeyMetadata']['KeyId']
            alias_name = re.sub('[^a-zA-Z0-9-]', '', alias_name).lower()
            self._client.create_alias(AliasName=f'alias/{alias_name}', TargetKeyId=key_id)
            self._put_key_policy(key_id)

            return key_id, alias_name

        except ClientError as e:
            log.exception(f'Error creating KMS key with alias: {e}')

    def _put_key_policy(self, key_id):
        response = self._client.get_key_policy(KeyId=key_id, PolicyName='default')
        policy = json.loads(response['Policy'])
        # The updated policy replaces the existing policy. Add a new statement to
        # the list along with the original policy statements.
        policy['Statement'].append(
            {
                'Sid': 'Allow access for PivotRole',
                'Effect': 'Allow',
                'Principal': {'AWS': '*'},
                'Action': [
                    'kms:Decrypt',
                    'kms:Encrypt',
                    'kms:GenerateDataKey*',
                    'kms:PutKeyPolicy',
                    'kms:GetKeyPolicy',
                    'kms:ReEncrypt*',
                    'kms:TagResource',
                    'kms:UntagResource',
                ],
                'Resource': '*',
                'Condition': {
                    'ArnLike': {'aws:PrincipalArn': f'arn:aws:iam::{self._account_id}:role/dataallPivotRole*'}
                },
            }
        )
        try:
            self._client.put_key_policy(KeyId=key_id, PolicyName='default', Policy=json.dumps(policy))
        except ClientError as err:
            log.exception(
                "Couldn't set policy for key %s. Here's why %s",
                key_id,
                err,
            )

    def delete_key_by_alias(self, alias_name):
        """
        Delete a KMS key by its alias.
        :param alias_name: Alias of the KMS key to be deleted
        :return: None
        """
        try:
            key_id = self._get_key_by_alias(alias_name)
            if key_id:
                # Schedule the key for deletion
                self._client.schedule_key_deletion(KeyId=key_id)
            self._client.delete_alias(AliasName=f'alias/{alias_name}')
        except ClientError as e:
            log.exception(f'Error deleting KMS key by alias: {e}')

    def _get_key_by_alias(self, alias_name):
        try:
            response = self._client.list_aliases()
            aliases = response.get('Aliases', [])

            for alias in aliases:
                if alias['AliasName'] == f'alias/{alias_name}':
                    key_id = alias['TargetKeyId']
                    return key_id
            return None

        except ClientError as e:
            log.exception(f'Error getting KMS key by alias: {e}')


class GlueClient:
    def __init__(self, session, region):
        self._client = session.client('glue', region_name=region)

    def get_database(self, database_name):
        """
        Check if a Glue database exists.
        :param database_name: Name of the Glue database to check
        :return: True if the database exists, False otherwise
        """
        try:
            database = self._client.get_database(Name=database_name)
            return database
        except self._client.exceptions.EntityNotFoundException:
            return False
        except ClientError as e:
            log.exception(f'Error checking if database {database_name} exists: {e}')

    def create_database(self, database_name, bucket):
        try:
            database_name = re.sub('[^a-zA-Z0-9_]', '', database_name).lower()
            self._client.create_database(DatabaseInput={'Name': database_name, 'LocationUri': f's3://{bucket}/'})
            return database_name
        except ClientError as e:
            log.exception(f'Error creating Glue database: {e}')

    def create_table(self, database_name, bucket, table_name):
        try:
            self._client.create_table(
                DatabaseName=database_name,
                TableInput={
                    'Name': table_name,
                    'Description': 'integration tests',
                    'StorageDescriptor': {
                        'Columns': [
                            {'Name': 'column1', 'Type': 'int'},
                            {'Name': 'column2', 'Type': 'string'},
                            {'Name': 'column3', 'Type': 'string'},
                        ],
                        'Location': f's3://{bucket}/{table_name}/',
                        'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
                        'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
                        'Compressed': False,
                        'SerdeInfo': {
                            'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe',
                            'Parameters': {'field.delim': ','},
                        },
                    },
                },
            )
        except ClientError as e:
            log.exception(f'Error creating Glue table: {e}')

    def delete_database(self, database_name):
        """
        Delete a Glue database.
        :param database_name: Name of the Glue database to be deleted
        :return: None
        """
        try:
            self._client.delete_database(Name=database_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityNotFoundException':
                log.exception(f"Glue database '{database_name}' does not exist.")
            else:
                log.exception(f'Error deleting Glue database: {e}')


class LakeFormationClient:
    def __init__(self, session, region):
        self._client = session.client('lakeformation', region_name=region)

    def add_role_to_datalake_admin(self, role_arn):
        try:
            response = self._client.get_data_lake_settings()
            existing_admins = response.get('DataLakeSettings', {}).get('DataLakeAdmins', [])
            if existing_admins:
                existing_admins = [admin['DataLakePrincipalIdentifier'] for admin in existing_admins]

            new_admins = [role_arn]
            new_admins.extend(existing_admins or [])
            self._client.put_data_lake_settings(
                DataLakeSettings={
                    'DataLakeAdmins': [
                        {'DataLakePrincipalIdentifier': principal} for principal in list(set(new_admins))
                    ]
                },
            )
            return existing_admins
        except ClientError as e:
            log.exception(f'Error granting lake formation permissions: {e}')

    def remove_role_from_datalake_admin(self, old_existing_principals):
        try:
            self._client.put_data_lake_settings(
                DataLakeSettings={
                    'DataLakeAdmins': [
                        {'DataLakePrincipalIdentifier': principal} for principal in old_existing_principals
                    ]
                },
            )
            return True
        except ClientError as e:
            log.exception(f'Error granting lake formation permissions: {e}')

    def grant_create_database(self, role_arn):
        """
        Grants permissions to create a Glue database in catalog.
        :param role_arn: principal to grant permissions
        :return: None
        """
        try:
            self._client.grant_permissions(
                Principal={'DataLakePrincipalIdentifier': role_arn},
                Resource={'Catalog': {}},
                Permissions=['CREATE_DATABASE'],
            )
            return True
        except ClientError as e:
            log.exception(f'Error granting permissions to create database: {e}')
