# Email Notification Provider implements the email notification service abstract method
import logging

from dataall.base.aws.cognito import Cognito
from dataall.base.aws.ses import Ses
from dataall.base.config import config
from dataall.core.notifications.services.email_notification_service import EmailNotificationService

log = logging.getLogger(__name__)

notification_configs = config.get_property('core.share_notifications')


class EmailNotificationProvider(EmailNotificationService):

    def __init__(self, dataset_owner_group, dataset_stewards, requester_group_name, requester_email_id, email_client) -> None:
        super().__init__()
        self.dataset_owner_group = dataset_owner_group
        self.dataset_stewards = dataset_stewards
        self.requester_group_name = requester_group_name
        self.requester_email_id = requester_email_id
        self.email_client = email_client

    # Implementation
    def send_email(self, to, message, subject):
        self.email_client.send_email(to, message, subject)

    @staticmethod
    def get_email_ids_from_groupList(group_list, identity_provider):
        email_list = set()
        for group in group_list:
            email_list.update(identity_provider.get_user_emailids_from_group(group))
        return email_list

    @staticmethod
    def get_email_provider_instance(datasetOwnerGroup, datasetStewards, requesterGroupName, requesterEmailId):
        return EmailNotificationProvider(datasetOwnerGroup, datasetStewards, requesterGroupName, requesterEmailId, Ses.get_ses_client())

    @staticmethod
    def send_email_task(requesterEmailId, subject, message, data):
        # Get instance of the email provider
        email_provider = EmailNotificationProvider.get_email_provider_instance(
            data.get('datasetOwnerGroup'),
            data.get('datasetStewardsGroup'),
            data.get('requesterGroupName'),
            requesterEmailId
        )
        try:
            identityProvider = Cognito()

            dataset_owner_group_email_list = email_provider.get_email_ids_from_groupList(
                [email_provider.dataset_owner_group, email_provider.dataset_stewards],
                identityProvider
            )

            if notification_configs['email']['features']['group_notifications'] == True:
                requester_group_email_list = email_provider.get_email_ids_from_groupList(
                    [email_provider.requester_group_name],
                    identityProvider
                )
            else:
                requester_group_email_list = [requesterEmailId]

            EmailNotificationProvider.send_email_to_users(dataset_owner_group_email_list, email_provider, message, subject)
            EmailNotificationProvider.send_email_to_users(requester_group_email_list, email_provider, message, subject)

        except Exception as e:
            raise e
        else:
            return True

    @staticmethod
    def send_email_to_users(email_list, email_provider, message, subject):
        # Send individual emails to all the email ids. Sending individual emails helps in tracking individual emails via message-ids
        # https://aws.amazon.com/blogs/messaging-and-targeting/how-to-send-messages-to-multiple-recipients-with-amazon-simple-email-service-ses/
        for emailId in email_list:
            email_provider.send_email([emailId], message, subject)
