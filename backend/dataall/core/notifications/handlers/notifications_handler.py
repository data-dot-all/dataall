
import logging

from dataall.core.notifications.services.email_notification_provider import EmailNotificationProvider
from dataall.core.tasks.service_handlers import Worker
from dataall.core.tasks.db.task_models import Task

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class NotificationHandler:

    @staticmethod
    @Worker.handler(path='notification.service')
    def notification_service(engine, task: Task):
        if task.payload.get('notificationType') == 'email':
            return NotificationHandler.send_email_notification(task)

    @staticmethod
    def send_email_notification(task: Task):
        try:
            log.info(f'Notification Service for Email Initiated .. for {task.payload.get("subject")}')
            requester_email_id = task.payload.get('shareRequestUserEmail')
            subject = task.payload.get('subject')
            message = task.payload.get('message')
            data = NotificationHandler.get_groups_dict(task.payload)
            return EmailNotificationProvider.send_email_task(requester_email_id, subject, message, data)
        except Exception as e:
            log.error(f'Error while sending email in the notification service -  {e})')
            raise e

    @staticmethod
    def get_groups_dict(task_payload):
        return {
            'datasetOwnerGroup': task_payload.get('datasetOwnerGroup'),
            'datasetStewardsGroup': task_payload.get('datasetStewardsGroup'),
            'requesterGroupName': task_payload.get('requesterGroupName')
        }
