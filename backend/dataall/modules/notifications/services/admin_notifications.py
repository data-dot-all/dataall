from typing import List

from dataall.modules.notifications.services.ses_email_notification_service import SESEmailNotificationService


class AdminNotificationService:
    admin_group = 'DAAdministrators'

    def notify_admins_with_error_log(self, process_error: str, error_logs: List[str], process_name:str = ''):

        subject = f'Data.all alert | Attention Required | Failure in : {process_name}'
        email_message = f"""
            Following error occurred - <br><br> {process_error} <br><br>
        """
        for error_log in error_logs:
            email_message += error_log + "<br><br>"

        email_message += "Please check the logs in cloudwatch for more details"

        SESEmailNotificationService.create_and_send_email_notifications(
            subject=subject,
            msg=email_message,
            recipient_groups_list=[AdminNotificationService.admin_group]
        )