import logging
import time

from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper

log = logging.getLogger('aws:ram')


class RamClient:
    def __init__(self, account_id, region):
        session = SessionHelper.remote_session(accountid=account_id, region=region)
        self._client = session.client('ram', region_name=region)
        self._account_id = account_id

    def _get_resource_share_invitations(self, resource_share_arns, sender_account, receiver_account):
        log.info(f'Listing invitations for resourceShareArns: {resource_share_arns}')
        try:
            resource_share_invitations = []

            paginator = self._client.get_paginator('get_resource_share_invitations')
            invitation_pages = paginator.paginate(resourceShareArns=resource_share_arns)
            for page in invitation_pages:
                resource_share_invitations.extend(page.get('resourceShareInvitations'))

            filtered_invitations = [
                i
                for i in resource_share_invitations
                if i['senderAccountId'] == sender_account and i['receiverAccountId'] == receiver_account
            ]
            return filtered_invitations
        except ClientError as e:
            log.error(f'Failed retrieving RAM resource share invitations {resource_share_arns} due to {e}')
            raise e

    def _accept_resource_share_invitation(self, resource_share_invitation_arn):
        try:
            response = self._client.accept_resource_share_invitation(
                resourceShareInvitationArn=resource_share_invitation_arn
            )
            log.info(f'Accepted ram invitation {resource_share_invitation_arn}')
            return response.get('resourceShareInvitation')
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceShareInvitationAlreadyAcceptedException':
                log.info(f'Failed to accept RAM invitation {resource_share_invitation_arn} already accepted')
            else:
                log.error(f'Failed to accept RAM invitation {resource_share_invitation_arn} due to {e}')
                raise e

    @staticmethod
    def check_ram_invitation_status(
        source_account_id, source_region, target_account_id, source_database, source_table_name
    ):
        source_ram = RamClient(source_account_id, source_region)

        resource_arn = f'arn:aws:glue:{source_region}:{source_account_id}:table/{source_database}/{source_table_name}'
        associations = source_ram._list_resource_share_associations(resource_arn)
        resource_share_arns = [a['resourceShareArn'] for a in associations if a['status'] == 'ASSOCIATED']

        if not len(resource_share_arns):
            return False

        resource_share_associations = []

        paginator = source_ram._client.get_paginator('get_resource_share_associations')
        association_pages = paginator.paginate(
            resourceShareArns=resource_share_arns, associationType='PRINCIPAL', principal=target_account_id
        )
        for page in association_pages:
            resource_share_associations.extend(page.get('resourceShareAssociations'))

        filtered_associations = [i for i in resource_share_associations if i['status'] == 'ASSOCIATED']

        log.info(
            f'Found {len(filtered_associations)} RAM associations for resourceShareArn: {resource_arn}'
            f'From Source Account {source_account_id} to Target Account {target_account_id}'
        )
        if not len(filtered_associations):
            return False
        return True

    @staticmethod
    def accept_ram_invitation(
        source_account_id, source_region, source_database, source_table_name, target_account_id, target_region
    ):
        """
        Accepts RAM invitations on the target account
        """
        retry_share_table = False
        failed_invitations = []

        if source_account_id == target_account_id:
            log.debug('Skipping RAM invitation management for same account sharing.')
            return True

        source_ram = RamClient(source_account_id, source_region)
        target_ram = RamClient(target_account_id, target_region)

        resource_arn = f'arn:aws:glue:{source_region}:{source_account_id}:table/{source_database}/{source_table_name}'
        associations = source_ram._list_resource_share_associations(resource_arn)
        resource_share_arns = [a['resourceShareArn'] for a in associations]

        ram_invitations = target_ram._get_resource_share_invitations(
            resource_share_arns, source_account_id, target_account_id
        )
        log.info(f'Found {len(ram_invitations)} RAM invitations for resourceShareArn: {resource_share_arns}')
        for invitation in ram_invitations:
            if 'LakeFormation' in invitation['resourceShareName']:
                if invitation['status'] == 'PENDING':
                    log.info(f'Invitation {invitation} is in PENDING status accepting it ...')
                    target_ram._accept_resource_share_invitation(invitation['resourceShareInvitationArn'])
                    # Ram invitation acceptance is slow
                    time.sleep(5)
                elif invitation['status'] == 'EXPIRED' or invitation['status'] == 'REJECTED':
                    log.warning(
                        f'Invitation {invitation} has expired or was rejected. '
                        'Table flagged for revoke re-share.'
                        'Deleting the resource share to reset the invitation... '
                    )
                    failed_invitations.append(invitation)
                    retry_share_table = True
                    source_ram._delete_resource_share(resource_share_arn=invitation['resourceShareArn'])

                elif invitation['status'] == 'ACCEPTED':
                    log.info(f'Invitation {invitation} already accepted nothing to do ...')
                else:
                    log.warning(
                        f'Invitation is in an unknown status adding {invitation["status"]}. '
                        'Adding it to retry share list ...'
                    )

        return retry_share_table, failed_invitations

    def _list_resource_share_associations(self, resource_arn):
        associations = []
        try:
            log.debug(f'RAM list_resource_share_associations : {resource_arn}')

            paginator = self._client.get_paginator('get_resource_share_associations').paginate(
                associationType='RESOURCE',
                resourceArn=resource_arn,
            )
            for page in paginator:
                associations.extend(page['resourceShareAssociations'])

            log.info(f'Found resource_share_associations : {associations}')
            return associations

        except ClientError as e:
            log.error(f'Could not find resource share associations for resource {resource_arn} due to: {e}')
            raise e

    def _delete_resource_share(self, resource_share_arn):
        self._client.delete_resource_share(resource_share_arn=resource_share_arn)
