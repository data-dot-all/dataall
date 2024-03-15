import logging
import os
import boto3

log = logging.getLogger(__name__)


class Ses:
    def __init__(self, fromEmailId: str = None):
        self.fromEmailId = fromEmailId
        self.client = boto3.client('sesv2', region_name=os.getenv('AWS_REGION', 'eu-west-1'))

    @staticmethod
    def get_ses_client():
        # Create SES client
        fromEmailId = os.getenv('email_sender_id', 'none')
        if fromEmailId != 'none':
            return Ses(fromEmailId)
        else:
            raise Exception('email_sender_id environment variable is not set')

    def send_email(self, toList, message, subject):
        # Get the SES client
        # Send the email
        try:
            ses_client = self.client
            destination_dict = {
                'ToAddresses': toList,
            }
            body_dict = {'Html': {'Data': message, 'Charset': 'UTF-8'}}
            subject_dict = {'Data': subject, 'Charset': 'UTF-8'}
            message_dict = {'Subject': subject_dict, 'Body': body_dict}

            return ses_client.send_email(
                FromEmailAddress=self.fromEmailId, Destination=destination_dict, Content={'Simple': message_dict}
            )
        except Exception as e:
            envname = os.getenv('envname', 'local')
            if envname in ['local', 'dkrcompose']:
                log.error('Local development environment does not support SES notifications')
                return True
            log.error(f'Error while sending email {e})')
            raise e
