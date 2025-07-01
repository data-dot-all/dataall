from dataall.core.tasks.service_handlers import Worker
from dataall.core.tasks.db.task_models import Task
from dataall.modules.metadata_forms.services.metadata_form_enforcement_service import MetadataFormEnforcementService


class EcsMetadataFormHandler:
    @staticmethod
    @Worker.handler(path='metadata_form.enforcement.notify')
    def notify_owners_of_enforcement(engine, task: Task):
        with engine.scoped_session() as session:
            MetadataFormEnforcementService.notify_owners_of_enforcement(
                session=session, rule_uri=task.targetUri, mf_name=task.payload.get('mf_name', 'Unknown name')
            )
