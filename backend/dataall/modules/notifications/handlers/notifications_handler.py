import logging

from dataall.core.tasks.service_handlers import Worker
from dataall.core.tasks.db.task_models import Task
from dataall.modules.notifications.services.ses_email_notification_service import SESEmailNotificationService

log = logging.getLogger(__name__)


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
            subject = task.payload.get('subject')
            message = task.payload.get('message')
            recipient_groups_list = task.payload.get('recipientGroupsList', [])
            recipient_email_list = task.payload.get('recipientEmailList', [])
            return SESEmailNotificationService.send_email_task(
                subject, message, recipient_groups_list, recipient_email_list
            )
        except Exception as e:
            log.error(f'Error while sending email in the notification service -  {e})')
            raise e
