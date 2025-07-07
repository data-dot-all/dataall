import logging
import os
import sys
import json
from dataall.base.db import get_engine
from collections import defaultdict
from typing import Dict, DefaultDict
from dataall.base.loader import load_modules, ImportMode
from dataall.base.services.service_provider_factory import ServiceProviderFactory
from dataall.modules.metadata_forms.db.metadata_form_repository import MetadataFormRepository
from dataall.modules.metadata_forms.services.metadata_form_enforcement_service import MetadataFormEnforcementService
from dataall.modules.notifications.services.ses_email_notification_service import SESEmailNotificationService
from dataall.modules.metadata_forms.db.enums import ENTITY_LINK_MAP


log = logging.getLogger(__name__)


def _get_affected_entities_per_user(session) -> DefaultDict[str, Dict[str, Dict[str, str]]]:
    """
    Iterate over all metadata forms to fetch all enforcement rules,
    and for each enforcement rule, identify affected entities without a metadata form attached.

    Gather entity owner information, resolve group owners to individual users,
    and prepare a mapping of users to the unique entities they own that are affected.

    Returns:
        A defaultdict where:
            - key = user email id (str)
            - value = dict mapping entity URI (str) to the entity object (dict with fields like name, type, owner, attached)
    """

    user_to_entities: DefaultDict[str, Dict[str, Dict[str, str]]] = defaultdict(dict)
    identityProvider = ServiceProviderFactory.get_service_provider_instance()

    # find all metadata forms
    all_mfs = MetadataFormRepository.query_user_metadata_forms(session, is_da_admin=True, groups=None, env_uris=None, org_uris=None, filter=None).all()
    log.info(f'Found {len(all_mfs)} metadata forms')

    # for a given form, get all enforcement rules
    for mf in all_mfs:
        log.info(f'Processing metadata form {mf.uri}')
        mf_enforcement_rules = MetadataFormRepository.list_mf_enforcement_rules(session, mf.uri)

        log.info(f'Found {len(mf_enforcement_rules)} enforcement rules for metadata form {mf.uri}')
        for rule in mf_enforcement_rules:
            log.info(f'Processing enforcement rule {rule.uri}')

            affected_entities = MetadataFormEnforcementService.get_affected_entities(uri=rule.uri, session=session)
            log.info(f'Found {len(affected_entities)} affected entities')

            for entity in affected_entities:
                if entity['attached'] is None:
                    if entity['owner']:
                        owner = entity["owner"]
                        log.info(f'Fetching members from entity owner {owner}')

                        try:
                            user_email_ids = identityProvider.get_user_emailids_from_group(groupName=owner)
                        except Exception as e:
                            # We consider individual owner as invalid for now
                            log.warning(f"Skipping invalid or missing owner group {owner}: {e}")
                            continue

                        if user_email_ids:
                            for email_id in user_email_ids:
                                user_to_entities[email_id][entity['uri']] = entity

    return user_to_entities


def send_reminder_email(engine):
    with engine.scoped_session() as session:
        log.info('Running Metadata Form Enforcement Email Alert Task')

        user_to_entities = _get_affected_entities_per_user(session)
        for email_id, entities in user_to_entities.items():
            email_body = _construct_email_body(entities.values())
            log.debug(f'Sending email to user: {email_id} with email content: {email_body}')
            subject = 'Action Required | Data.all metadata compliance digest'

            try:
                SESEmailNotificationService.send_email_task(
                    subject=subject, message=email_body, recipient_groups_list=[], recipient_email_list=[email_id]
                )
            except Exception as e:
                err_msg = f'Failed to send email in weekly metadata form enforcement reminder task due to: {e}'
                log.exception(err_msg)

        log.info('Completed Metadata Form Enforcement Email Alert Task')


def _construct_email_body(entities):

    msg_heading = f"""Dear User, <br><br>

               The following resources that you own in Data.all are missing one or more required metadata forms.
               Please review them and attach the necessary metadata forms to ensure compliance.<br><br>
               """

    msg_content = _create_table_for_resource(entities)

    msg_footer = """Your prompt attention in this matter is greatly appreciated.
                 <br><br>Best regards,
                 <br>The Data.all Team
                 """

    return msg_heading + msg_content + msg_footer


def _create_table_for_resource(entities):
    table_heading = """
    <tr>
        <th align='center'>
            Entity Type
        </th>
        <th align='center'>
            Name
        </th>
         <th align='center'>
            Link
        </th>
    </tr>
    """
    table_body = """"""

    for entity in entities:
        entity_type = entity["type"]

        # get entity link
        if entity_type in ENTITY_LINK_MAP:
            entity_link = f'/console/{ENTITY_LINK_MAP[entity_type]}/{entity["uri"]}'
            entity_link_text = f'<a href="{os.environ.get("frontend_domain_url", "") + entity_link}">View Resource</a>'
        else:
            entity_link_text = "N/A"

        table_body += f"""
            <tr>
                <td align='center'>
                    {entity['type']}
                </td>
                <td align='center'>
                    {entity['name']}
                </td>
                 <td align='center'>
                    {entity_link_text}
                </td>
            </tr>
        """
    table = f"""
    <table border='1' style='border-collapse:collapse; width: 70%;'>
        {table_heading}
        {table_body}
    </table>
    <br>
    <br>
    """

    return table


if __name__ == '__main__':
    load_modules(modes={ImportMode.API})
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    send_reminder_email(engine=ENGINE)
