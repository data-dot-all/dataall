import logging
import time

from botocore.exceptions import ClientError

from .sts import SessionHelper

log = logging.getLogger('aws:ram')


class Ram:
    @staticmethod
    def get_resource_share_invitations(
        client, resource_share_arns, sender_account, receiver_account
    ):
        log.info(f'Listing invitations for resourceShareArns: {resource_share_arns}')
        try:
            resource_share_invitations = []

            paginator = client.get_paginator('get_resource_share_invitations')
            invitation_pages = paginator.paginate(resourceShareArns=resource_share_arns)
            for page in invitation_pages:
                resource_share_invitations.extend(page.get('resourceShareInvitations'))

            filtered_invitations = [
                i
                for i in resource_share_invitations
                if i['senderAccountId'] == sender_account
                and i['receiverAccountId'] == receiver_account
            ]
            return filtered_invitations
        except ClientError as e:
            log.error(
                f'Failed retrieving RAM resource '
                f'share invitations {resource_share_arns} due to {e}'
            )
            raise e

    @staticmethod
    def accept_resource_share_invitation(client, resource_share_invitation_arn):
        try:
            response = client.accept_resource_share_invitation(
                resourceShareInvitationArn=resource_share_invitation_arn
            )
            log.info(f'Accepted ram invitation {resource_share_invitation_arn}')
            return response.get('resourceShareInvitation')
        except ClientError as e:
            if (
                e.response['Error']['Code']
                == 'ResourceShareInvitationAlreadyAcceptedException'
            ):
                log.info(
                    f'Failed to accept RAM invitation '
                    f'{resource_share_invitation_arn} already accepted'
                )
            else:
                log.error(
                    f'Failed to accept RAM invitation '
                    f'{resource_share_invitation_arn} due to {e}'
                )
                raise e

    @staticmethod
    def accept_ram_invitation(**data):
        """
        Accepts RAM invitations on the target account
        """
        retry_share_table = False
        failed_invitations = []
        source = data['source']
        target = data['target']

        if source['accountid'] == target['accountid']:
            log.debug('Skipping RAM invitation management for same account sharing.')
            return True

        source_session = SessionHelper.remote_session(accountid=source['accountid'])
        source_ram = source_session.client('ram', region_name=source['region'])

        target_session = SessionHelper.remote_session(accountid=target['accountid'])
        target_ram = target_session.client('ram', region_name=target['region'])

        resource_arn = (
            f'arn:aws:glue:{source["region"]}:{source["accountid"]}:'
            f'table/{data["source"]["database"]}/{data["source"]["tablename"]}'
        )
        associations = Ram.list_resource_share_associations(source_ram, resource_arn)
        resource_share_arns = [a['resourceShareArn'] for a in associations]

        ram_invitations = Ram.get_resource_share_invitations(
            target_ram, resource_share_arns, source['accountid'], target['accountid']
        )
        log.info(
            f'Found {len(ram_invitations)} RAM invitations for resourceShareArn: {resource_share_arns}'
        )
        for invitation in ram_invitations:
            if 'LakeFormation' in invitation['resourceShareName']:
                if invitation['status'] == 'PENDING':
                    log.info(
                        f'Invitation {invitation} is in PENDING status accepting it ...'
                    )
                    Ram.accept_resource_share_invitation(
                        target_ram, invitation['resourceShareInvitationArn']
                    )
                    # Ram invitation acceptance is slow
                    time.sleep(5)
                elif (
                    invitation['status'] == 'EXPIRED'
                    or invitation['status'] == 'REJECTED'
                ):
                    log.warning(
                        f'Invitation {invitation} has expired or was rejected. '
                        'Table flagged for revoke re-share.'
                        'Deleting the resource share to reset the invitation... '
                    )
                    failed_invitations.append(invitation)
                    retry_share_table = True
                    source_ram.delete_resource_share(
                        resourceShareArn=invitation['resourceShareArn']
                    )

                elif invitation['status'] == 'ACCEPTED':
                    log.info(
                        f'Invitation {invitation} already accepted nothing to do ...'
                    )
                else:
                    log.warning(
                        f'Invitation is in an unknown status adding {invitation["status"]}. '
                        'Adding it to retry share list ...'
                    )

        return retry_share_table, failed_invitations

    @staticmethod
    def list_resource_share_associations(client, resource_arn):
        associations = []
        try:
            log.debug(f'RAM list_resource_share_associations : {resource_arn}')

            paginator = client.get_paginator(
                'get_resource_share_associations'
            ).paginate(
                associationType='RESOURCE',
                resourceArn=resource_arn,
            )
            for page in paginator:
                associations.extend(page['resourceShareAssociations'])

            log.info(f'Found resource_share_associations : {associations}')
            return associations

        except ClientError as e:
            log.error(
                f'Could not find resource share associations for resource {resource_arn} due to: {e}'
            )
            raise e

    @staticmethod
    def delete_resource_shares(client, resource_arn):
        log.info(f'Cleaning RAM resource shares for resource: {resource_arn}')
        try:
            associations = Ram.list_resource_share_associations(client, resource_arn)
            for a in associations:
                log.info(f"Deleting resource share: {a['resourceShareArn']}")
                client.delete_resource_share(resourceShareArn=a['resourceShareArn'])
            return associations
        except ClientError as e:
            log.error(f'Failed cleaning RAM resource shares due to: {e} ')

    @staticmethod
    def delete_lfv1_resource_shares_for_table(client, resource_arn):
        log.info(f'Cleaning LF V1 RAM resource shares for resource: {resource_arn}')
        try:
            associations = Ram.list_resource_share_associations(client, resource_arn)
            for a in associations:
                if (
                    'LakeFormation' in a['resourceShareName']
                    and 'LakeFormation-V2' in a['resourceShareName']
                ):
                    log.info(
                        f"Found lakeformation V1 RAM association: {a['resourceShareName']}."
                        'Deleting it ...'
                    )
                    client.delete_resource_share(resourceShareArn=a['resourceShareArn'])
            return associations
        except ClientError as e:
            log.error(f'Failed cleaning RAM resource shares due to: {e} ')

    @staticmethod
    def delete_lakeformation_v1_resource_shares(client):
        log.info('Cleaning LF V1 RAM resource shares...')

        try:
            resources = []
            paginator = client.get_paginator('list_resources').paginate(
                resourceOwner='SELF',
                resourceRegionScope='REGIONAL',
            )
            for page in paginator:
                resources.extend(page['resources'])

            log.info(f'Found resources : {len(resources)}')
            resource_shares = []
            for r in resources:
                paginator = client.get_paginator('get_resource_shares').paginate(
                    resourceShareArns=[r['resourceShareArn']],
                    resourceOwner='SELF',
                )
                for page in paginator:
                    resource_shares.extend(page['resourceShares'])
                for rs in resource_shares:
                    if (
                        'LakeFormation' in rs['name']
                        and 'LakeFormation-V2' not in rs['name']
                    ):
                        log.info(
                            f"Found lakeformation V1 RAM association: {rs['name']}."
                            'Deleting it ...'
                        )
                        client.delete_resource_share(
                            resourceShareArn=r['resourceShareArn']
                        )

        except ClientError as e:
            log.error(f'Failed cleaning RAM resource shares due to: {e} ')
