import logging
import PyPDF2
from io import BytesIO

from dataall.base.aws.sts import SessionHelper
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self, account_id, region, env_group, aws_account_id):
        base_session = SessionHelper.remote_session(accountid=aws_account_id, region=region)
        session = SessionHelper.get_session(base_session=base_session, role_arn=env_group.environmentIAMRoleArn)
        self._client = session.client('s3', region_name=region)
        self.region = region
        self._account_id = account_id

    def list_object_keys(self, bucket_name):
        
        try:
            response = self._client.list_objects_v2(
                Bucket=bucket_name,
            )

            def txt_or_pdf(s):
                suffix = s.split('.')[-1]
                if suffix == 'pdf' or suffix == 'txt':
                    return True
                else:
                    return False

            return ' '.join([ob['Key'] for ob in response.get('Contents', []) if txt_or_pdf(ob['Key'])])
        except ClientError as e:
            logging.error(f'Failed to list objects in {bucket_name} : {e}')
            raise e

    def get_content(self, bucket_name, key):
        try:
            response = self._client.get_object(Bucket=bucket_name, Key=key)
            if bucket_name.split('.')[-1] == 'txt':
                file_content = response['Body'].read().decode('utf-8')
                return file_content
            else:
                pdf_content = response['Body'].read()
                pdf_buffer = BytesIO(pdf_content)
                pdf_reader = PyPDF2.PdfReader(pdf_buffer)
                full_text = ''
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    full_text += page.extract_text()
                return full_text

        except ClientError as e:
            logging.error(f'Failed to get content of {key} in {bucket_name} : {e}')
            raise e
