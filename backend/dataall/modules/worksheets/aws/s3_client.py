import logging
import PyPDF2
from io import BytesIO

from dataall.base.aws.sts import SessionHelper
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Client:
    file_extension_readers = {
        'txt': lambda content: S3Client._read_txt_content(content),
        'pdf': lambda content: S3Client._read_pdf_content(content),
    }

    def __init__(self, account_id, region, role=None):
        aws_session = SessionHelper.remote_session(accountid=account_id, region=region, role=role)
        self._client = aws_session.client('s3', region_name=region)

    @staticmethod
    def _read_txt_content(content):
        file_content = content['Body'].read().decode('utf-8')
        return file_content

    @staticmethod
    def _read_pdf_content(content):
        pdf_content = content['Body'].read()
        pdf_buffer = BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_buffer)
        full_text = ''
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            full_text += page.extract_text()

    def get_content(self, bucket_name, key):
        try:
            file_extension = key.split('.')[-1].lower()
            if file_extension not in self.file_extension_readers.keys():
                raise Exception('Unsupported file type')

            content = self._client.get_object(Bucket=bucket_name, Key=key)

            return self.file_extension_readers[file_extension](content)

        except ClientError as e:
            logging.error(f'Failed to get content of {key} in {bucket_name} : {e}')
            raise e
