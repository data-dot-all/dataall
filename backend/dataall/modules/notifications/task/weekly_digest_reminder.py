import logging
import os
from typing import List, Dict

from dataall.base.db import get_engine
from dataall.base.loader import load_modules, ImportMode
from dataall.core.environment.db.environment_models import Environment
from dataall.core.stacks.api.enums import StackStatus
from dataall.core.stacks.db.stack_repositories import StackRepository
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.notifications.services.admin_notifications import AdminNotificationService
from dataall.modules.notifications.services.ses_email_notification_service import SESEmailNotificationService
from dataall.modules.shares_base.db.share_object_models import ShareObject
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.services.shares_enums import ShareItemHealthStatus

log = logging.getLogger(__name__)


class ResourceBundle:
    def __init__(self):
        self.share_object_list = []
        self.dataset_object_list = []
        self.environment_object_list = []
def send_reminder_email(engine):
    task_exceptions = []
    try:
        with engine.scoped_session() as session:
            # Get all the shares which are in unhealthy state

            # Todo : Check if distinct needed for the shareobject repository
            unhealthy_share_objects: List[ShareObject] = ShareObjectRepository.get_share_object_with_health_status(session=session, health_status_list=[ShareItemHealthStatus.Unhealthy.value])

            # Get all the dataset which are in unhealthy state
            all_datasets: List[DatasetBase] = session.query(DatasetBase).all()
            unhealthy_datasets: List[DatasetBase] = []
            unhealthy_stack_status: List[StackStatus] = [
                StackStatus.CREATE_FAILED.value,
                StackStatus.DELETE_FAILED.value,
                StackStatus.UPDATE_FAILED.value,
                StackStatus.UPDATE_ROLLBACK_FAILED.value,
                StackStatus.ROLLBACK_FAILED.value
            ]
            for dataset in all_datasets:
                if StackRepository.find_stack_by_target_uri(session=session, target_uri=dataset.datasetUri, statuses=unhealthy_stack_status) is not None:
                    unhealthy_datasets.append(dataset)

            # Get all the environments which are in unhealthy state
            all_environments: List[Environment] = session.query(Environment).all()
            unhealthy_environments: List[Environment] = []
            for environment in all_environments:
                if StackRepository.find_stack_by_target_uri(session=session, target_uri=environment.environmentUri, statuses=unhealthy_stack_status) is not None:
                    unhealthy_environments.append(environment)

            # {team: ResourceBundle}
            group_name_to_resource_map: Dict[str, ResourceBundle] = {}
            def _map_teams_to_resources(list_of_resources, group_attr, resource_type):
                for resource in list_of_resources:
                    group_name = resource.__getattribute__(group_attr)
                    if group_name not in group_name_to_resource_map:
                        resource_bundle = ResourceBundle()
                        resource_bundle.__getattribute__(resource_type).append(resource)
                        group_name_to_resource_map[group_name] = resource_bundle
                    else:
                        resource_bundle = group_name_to_resource_map.get(group_name)
                        resource_bundle.__getattribute__(resource_type).append(resource)

            _map_teams_to_resources(list_of_resources=unhealthy_share_objects, group_attr="groupUri", resource_type="share_object_list")
            _map_teams_to_resources(list_of_resources=unhealthy_environments, group_attr="SamlGroupName", resource_type="environment_object_list")
            _map_teams_to_resources(list_of_resources=unhealthy_datasets, group_attr="SamlAdminGroupName", resource_type="dataset_object_list")

            for group, resource_bundle in group_name_to_resource_map.items():
                email_body = _construct_email_body(resource_bundle)
                subject = 'Attention Required | Data.all weekly digest'
                try:
                    SESEmailNotificationService.create_and_send_email_notifications(subject=subject, msg=email_body, recipient_groups_list=[group])
                except Exception as e:
                    log.error(f"Error occurred in sending email while weekly reminder task due to: {e}")
                    task_exceptions.append(f"Error occurred in sending email while weekly reminder task due to: {e}")
    except Exception as e:
        log.error(f"Error occurred while running the weekly reminder task: {e}")
        task_exceptions.append(f"Error occurred while running the weekly reminder task: {e}")
    finally:
        if len(task_exceptions) > 0:
            AdminNotificationService().notify_admins_with_error_log(
                process_error="Error occured while running the weekly reminder task",
                error_logs=task_exceptions,
                process_name="Weekly reminder task"
            )


def _construct_email_body(resource_bundle: ResourceBundle):
    msg_heading = """
    Dear Team, <br>
    You have following data.all resources in unhealthy state. Please click on the links provided to get to the affected resource.
    Please correct affected resources ASAP. <br><br> 
    
    For shares which are in unhealthy state, you can re-apply share by clicking on the "Reapply share" button <br>
    For environments and datasets which are in unhealthy state, you can go to the AWS account and check the stack associated with that environment and check the root cause of the stack. Once you address the root cause issue, you can click on "Update Stack" on the Stack Page. <br> 
    """
    msg_content = """"""
    share_object_table_content = _create_table_for_resource(resource_bundle.share_object_list, "shareUri", "/console/shares/", "Share Object")
    dataset_object_table_content = _create_table_for_resource(resource_bundle.dataset_object_list, "datasetUri", "/console/s3-datasets/", "Dataset")
    environment_object_table_content = _create_table_for_resource(resource_bundle.environment_object_list, "environmentUri", "/console/environments/", "Environment")

    msg_content += share_object_table_content + "<br><br>" + dataset_object_table_content + "<br><br>" + environment_object_table_content + "<br><br>"

    msg_footer = """
    In case your stack(s) or share object is still in unhealthy state after applying remedial measures, please contact data.all team. <br><br>
    Regards,<br>
    data.all Team
    """

    return msg_heading + msg_content + msg_footer

def _create_table_for_resource(list_of_resources, uri_attr, link_uri, object_type):
    table_heading = """
    <tr>    
        <th>
            Type
        </th>
         <th>
            Link
        </th>
    </tr>
    """
    table_body = """"""
    for resource in list_of_resources:
        table_body += f"""
            <tr>
                <td>
                    {object_type}
                </td>
                 <td>
                    {os.environ.get('frontend_domain_url', '') + link_uri + resource.__getattribute__(uri_attr)}
                </td>
            </tr>
            <>
        """
    table = f"""
    <table>
        {table_heading}
        {table_body}
    </table>
    """

    return table



if __name__ == '__main__':
    log.info("Starting weekly reminders task")
    load_modules(modes={ImportMode.SHARES_TASK})
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    send_reminder_email(engine=ENGINE)
