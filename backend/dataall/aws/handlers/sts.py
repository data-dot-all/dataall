import json
import logging
import os
import urllib

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from dataall.version import __version__, __pkg_name__

try:
    from urllib import quote_plus
    from urllib2 import urlopen
except ImportError:
    from urllib.parse import quote_plus
    from urllib.request import urlopen


log = logging.getLogger(__name__)


class SessionHelper:
    """SessionHelpers is a class simplifying common aws boto3 session tasks and helpers"""

    @classmethod
    def get_root_account_session(cls):
        ENVNAME = os.environ.get('envname', 'local')

    @classmethod
    def get_session(cls, base_session=None, role_arn=None):
        """Returns a boto3 session fo the given role
        Args:
            base_session(object,optional) :  a boto3 session
            role_arn(string, optional) : a role arn
        Returns:
            boto3.session.Session : a boto3 session
                    If neither base_session and role_arn is provided, returns a default boto3 session
                    If role_arn is provided, base_session should be a boto3 session on the aws accountid is defined
        """
        if role_arn:
            external_id_secret = cls.get_external_id_secret()
            if external_id_secret:
                assume_role_dict = dict(
                    RoleArn=role_arn,
                    RoleSessionName=role_arn.split('/')[1],
                    ExternalId=external_id_secret,
                )
            else:
                assume_role_dict = dict(
                    RoleArn=role_arn,
                    RoleSessionName=role_arn.split('/')[1],
                )
            try:
                sts = base_session.client(
                    'sts',
                    config=Config(user_agent_extra=f'{__pkg_name__}/{__version__}'),
                )
                response = sts.assume_role(**assume_role_dict)
                return boto3.Session(
                    aws_access_key_id=response['Credentials']['AccessKeyId'],
                    aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                    aws_session_token=response['Credentials']['SessionToken'],
                )
            except ClientError as e:
                log.error(f'Failed to assume role {role_arn} due to: {e} ')
                raise e

        else:
            return boto3.Session()

    @classmethod
    def get_secret(cls, secret_name):
        """
        Method to get secret_string from secrets manager
        :return:
        :rtype:
        """
        secret_string = None
        region = os.getenv('AWS_REGION', 'eu-west-1')
        try:
            session = SessionHelper.get_session()
            client = session.client('secretsmanager', region_name=region)
            secret_string = client.get_secret_value(SecretId=secret_name).get('SecretString')
            log.debug(f'Found Secret {secret_name}|{secret_string}')
        except ClientError as e:
            log.warning(f'Secret {secret_name} not found: {e}')
        return secret_string

    @classmethod
    def get_external_id_secret(cls):
        """
        External Id used to secure dataall pivot role
        sts:AssumeRole operation on onboarded environments
        :return:
        :rtype:
        """
        return SessionHelper.get_secret(secret_name=f'dataall-externalId-{os.getenv("envname", "local")}')

    @classmethod
    def get_delegation_role_name(cls):
        """Returns the role name that this package assumes on remote accounts
        Returns:
            string: name of the assumed role
        """
        return SessionHelper.get_secret(secret_name=f'dataall-pivot-role-name-{os.getenv("envname", "local")}')

    @classmethod
    def get_console_access_url(cls, boto3_session, region='eu-west-1', bucket=None, redshiftcluster=None):
        """Returns an AWS Console access url for the boto3 session
        Args:
            boto3_session(object): a boto3 session
        Returns:
                String: aws federated access console url
        """
        c = boto3_session.get_credentials()
        json_string_with_temp_credentials = '{'
        json_string_with_temp_credentials += '"sessionId":"' + c.access_key + '",'
        json_string_with_temp_credentials += '"sessionKey":"' + c.secret_key + '",'
        json_string_with_temp_credentials += '"sessionToken":"' + c.token + '"'
        json_string_with_temp_credentials += '}'

        request_parameters = '?Action=getSigninToken'
        # request_parameters = "&SessionDuration=43200"
        request_parameters += '&Session=' + urllib.parse.quote_plus(json_string_with_temp_credentials)
        request_url = 'https://signin.aws.amazon.com/federation' + request_parameters

        r = urllib.request.urlopen(request_url).read()

        signin_token = json.loads(r)
        request_parameters = '?Action=login'
        request_parameters += '&Issuer=Example.org'
        if bucket:
            request_parameters += '&Destination=' + quote_plus(
                'https://{}.console.aws.amazon.com/s3/buckets/{}/'.format(region, bucket)
            )

        elif redshiftcluster:
            request_parameters += '&Destination=' + quote_plus(
                f'https://{region}.console.aws.amazon.com/redshiftv2/' f'home?region={region}#query-editor:'
            )
        else:
            request_parameters += '&Destination=' + urllib.parse.quote_plus(f'https://{region}.console.aws.amazon.com/')
        request_parameters += '&SigninToken=' + signin_token['SigninToken']
        request_url = 'https://signin.aws.amazon.com/federation' + request_parameters

        # Send final URL to stdout
        return request_url

    @classmethod
    def get_delegation_role_arn(cls, accountid):
        """Returns the name that will be assumed to perform IAM actions on a given AWS accountid
        Args:
            accountid(string) : aws account id
        Returns:
                string : arn of the delegation role on the target aws account id
        """
        return 'arn:aws:iam::{}:role/{}'.format(accountid, cls.get_delegation_role_name())

    @classmethod
    def get_cdk_look_up_role_arn(cls, accountid, region):
        """Returns the name that will be assumed to perform IAM actions on a given AWS accountid using CDK Toolkit role
        Args:
            accountid(string) : aws account id
        Returns:
                string : arn of the CDKToolkit role on the target aws account id
        """
        print(f"Getting CDK look up role: arn:aws:iam::{accountid}:role/cdk-hnb659fds-lookup-role-{accountid}-{region}")
        return 'arn:aws:iam::{}:role/cdk-hnb659fds-lookup-role-{}-{}'.format(accountid, accountid, region)

    @classmethod
    def get_delegation_role_id(cls, accountid):
        """Returns the name that will be assumed to perform IAM actions on a given AWS accountid
        Args:
            accountid(string) : aws account id
        Returns :
            string : RoleId of the role
        """
        session = SessionHelper.remote_session(accountid=accountid)
        client = session.client('iam', region_name='eu-west-1')
        response = client.get_role(RoleName=cls.get_delegation_role_name())
        return response['Role']['RoleId']

    @classmethod
    def remote_session(cls, accountid, cdkrole=None, region=None):
        """Creates a remote boto3 session on the remote AWS account , assuming the delegation Role
        Args:
            accountid(string) : aws account id
            cdkrole(bool) : flag to use cdk look up role instead of pivot role
            region(string) : aws region
        Returns :
            boto3.session.Session: boto3 Session, on the target aws accountid, assuming the delegation role
        """
        base_session = cls.get_session()
        if cdkrole:
            log.info(f"Remote boto3 session using cdk_look_up_role_arn for account={accountid} and region={region}")
            role_arn = cls.get_cdk_look_up_role_arn(accountid=accountid, region=region)
        else:
            log.info(f"Remote boto3 session using pivot role for account= {accountid}")
            role_arn = cls.get_delegation_role_arn(accountid=accountid)
        session = SessionHelper.get_session(base_session=base_session, role_arn=role_arn)
        return session

    @classmethod
    def get_account(cls, session=None):
        """Returns the aws account id associated with the default session, or the provided session
        Args:
            session(object, optional) : boto3 session
        Returns :
            string: AWS Account id of the provided session,
                or the default boto3 session is not session argument was provided
        """
        if not session:
            session = cls.get_session()
        client = session.client('sts')
        response = client.get_caller_identity()
        return response['Account']

    @classmethod
    def get_organization_id(cls, session=None):
        """Returns the organization id for the priovided session
        Args:
            session(object) : boto3 session
        Returns
            string : AWS organization id
        """
        if not session:
            session = cls.get_session()
        client = session.client('organizations')
        response = client.describe_organization()
        return response['Organization']['Id']

    @staticmethod
    def get_role_id(accountid, name):
        session = SessionHelper.remote_session(accountid=accountid)
        client = session.client('iam')
        try:
            response = client.get_role(RoleName=name)
            return response['Role']['RoleId']
        except ClientError:
            return None

    @staticmethod
    def extract_account_from_role_arn(arn):
        """takes a role arn and returns its account id
        Args :
            arn(str) : role arn
        Return :
            str : account id or none if arn could not be parsed
        """
        try:
            return arn.split(':')[4]
        except Exception:
            return None

    @staticmethod
    def extract_name_from_role_arn(arn):
        """Extract the role name from a Role arn
        Args :
            arn(str) : role arn
        Return :
            str : name of the role, or none if arn could not be parsed
        """
        try:
            return arn.split('/')[-1]
        except Exception:
            return None

    @staticmethod
    def filter_roles_in_account(accountid, arns):
        """
        Filter roles in a given account
        Args :
            accountid(str) : aws account number
            arns(list) : a list of arns
        Return :
            list : list of all arns within the account
        """
        return [arn for arn in arns if SessionHelper.extract_account_from_role_arn(arn) == accountid]

    @staticmethod
    def get_role_ids(accountid, arns):
        """
        Returns the list of Role ids for the list of arns existing within the provided aws account  number
        Args :
            accountid(str) : aws account number
            arns(list) : a list of arns
        Return :
            list : list of Role ids for role which arn are in the same aws account
        """
        arns_in_account = SessionHelper.filter_roles_in_account(accountid, arns)
        potentially_none = [
            SessionHelper.get_role_id(
                accountid=accountid,
                name=SessionHelper.extract_name_from_role_arn(role_arn),
            )
            for role_arn in arns_in_account
        ]
        return [roleid for roleid in potentially_none if roleid]

    @classmethod
    def get_session_by_access_key_and_secret_key(cls, access_key_id, secret_key):
        """Returns a boto3 session fo the access_key_id and secret_key
        Args:
            access_key_id(string,required)
            secret_key(string, required)
        Returns:
            boto3.session.Session : a boto3 session
        """
        if not access_key_id or not secret_key:
            raise ValueError('Passed access_key_id and secret_key are invalid')

        return boto3.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_key)

    @staticmethod
    def generate_console_url(credentials, session_duration=None, region='eu-west-1', bucket=None):
        json_string_with_temp_credentials = '{'
        json_string_with_temp_credentials += '"sessionId":"' + credentials['AccessKeyId'] + '",'
        json_string_with_temp_credentials += '"sessionKey":"' + credentials['SecretAccessKey'] + '",'
        json_string_with_temp_credentials += '"sessionToken":"' + credentials['SessionToken'] + '"'
        json_string_with_temp_credentials += '}'

        request_parameters = '?Action=getSigninToken'
        if session_duration:
            request_parameters += '&SessionDuration={}'.format(session_duration)
        request_parameters += '&Session=' + quote_plus(json_string_with_temp_credentials)
        request_url = 'https://signin.aws.amazon.com/federation' + request_parameters

        r = urlopen(request_url).read()

        signin_token = json.loads(r)
        request_parameters = '?Action=login'
        request_parameters += '&Issuer=Example.org'
        if bucket:
            request_parameters += '&Destination=' + quote_plus(
                'https://{}.console.aws.amazon.com/s3/buckets/{}/'.format(region, bucket)
            )
        else:
            request_parameters += '&Destination=' + quote_plus('https://{}.console.aws.amazon.com/'.format(region))
        request_parameters += '&SigninToken=' + signin_token['SigninToken']
        request_url = 'https://signin.aws.amazon.com/federation' + request_parameters

        # Send final URL to stdout
        return request_url
