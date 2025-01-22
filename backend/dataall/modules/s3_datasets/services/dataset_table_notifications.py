from typing import Dict, List
import logging
from dataall.modules.notifications.services.ses_email_notification_service import SESEmailNotificationService
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset, DatasetTable
from dataall.modules.s3_datasets.db.dataset_table_repositories import DatasetTableShareDetails
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository

log = logging.getLogger(__name__)


class DatasetTableNotifications:
    def __init__(self, dataset: S3Dataset):
        self.dataset: S3Dataset = dataset

    """
    Sends email notification on glue table updates to the dataset owners. 
    Also, if there exists shares on that dataset, then send email notifications to the requestors informing updates
    table_status_map - Dictionary of GlueTableName and table status ( InSync, Deleted, etc ) 
    """

    def notify_dataset_table_updates(self, dataset_table_status_map: Dict[DatasetTable, DatasetTableShareDetails]):
        self._send_email_reminders_for_dataset(dataset_table_status_map)

        for dataset_table, table_share_details in dataset_table_status_map.items():
            share_on_tables = table_share_details.share_objects
            if share_on_tables:
                for share in share_on_tables:
                    self._send_email_notification_for_share(share, dataset_table_status_map)

    def _send_email_notification_for_share(self, share, dataset_table_status_map):
        subject = f'Alert: Data.all Update | Glue table(s) updated for dataset: {self.dataset.name}'
        msg_footer = f"""
                    You have an active share with uri: {share.shareUri}. If there are any table(s) requested by you on the dataset: {self.dataset.name}, then for that share the table might be affected <b>in case the tables were deleted.</b><br> 
                    <br><b>Note</b>: Please check with the dataset owner if there is any missing table from your share - as it is likely deleted from the dataset.<br> If the table exists in the dataset and is successfully shared but you are unable to access the table, then please reach out to the data.all team<br><br>
                    Regards,<br>
                    data.all team 
                """
        table_content = self._construct_html_table_from_glue_status_map(dataset_table_status_map)
        msg_body = f"""
                Dear Team,<br><br> 
                Following tables have been updated for dataset: <b>{self.dataset.name}</b> <br><br>

                {table_content}<br><br>
                """
        msg = msg_body + msg_footer
        SESEmailNotificationService.create_and_send_email_notifications(
            subject=subject, msg=msg, recipient_groups_list=[share.groupUri]
        )

    def _send_email_reminders_for_dataset(self, table_status_map):
        subject = f'Data.all Update | Glue table(s) updated for dataset: {self.dataset.name}'
        table_content = self._construct_html_table_from_glue_status_map(table_status_map)
        msg_body = f"""
        Dear Team,<br><br> 
        Following tables have been updated for dataset: <b>{self.dataset.name}</b>. <br><br>
        
        {table_content}<br><br>
        """
        msg_footer = """
        Regards,<br>
        data.all team
        """
        msg = msg_body + msg_footer
        SESEmailNotificationService.create_and_send_email_notifications(
            subject=subject, msg=msg, recipient_groups_list=[self.dataset.SamlAdminGroupName, self.dataset.stewards]
        )

    @classmethod
    def _construct_html_table_from_glue_status_map(cls, dataset_table_status_map):
        table_heading = """
        <tr>    
            <th align='center'>Glue Table Name</th>
            <th align='center'>Status</th>
        </tr>
        """
        table_body = """"""
        for dataset_table, dataset_table_details in dataset_table_status_map.items():
            table_body += f"""
                <tr>
                    <td align='center'>{dataset_table.GlueTableName}</td>
                    <td align='center'>{dataset_table_details.status}</td>
                </tr>
            """
        table_content = f"""
        <table border='1' style='border-collapse:collapse'>
            {table_heading}
            {table_body}
        </table>
        """
        return table_content
