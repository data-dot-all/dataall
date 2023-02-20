import logging

from sqlalchemy import and_, or_, func, case

from . import (
    has_resource_perm,
    ResourcePolicy,
    Environment,
)
from .. import api, utils
from .. import models, exceptions, permissions, paginate
from ..models.Enums import ShareObjectStatus, ShareItemStatus, ShareObjectActions, ShareItemActions, ShareableType, PrincipalType

logger = logging.getLogger(__name__)


class Transition:
    def __init__(self, name, transitions):
        self._name = name
        self._transitions = transitions
        self._all_source_states = [*set([item for sublist in transitions.values() for item in sublist])]
        self._all_target_states = [item for item in transitions.keys()]

    def validate_transition(self, prev_state):
        if prev_state in self._all_target_states:
            logger.info(f'Resource is already in target state ({prev_state}) in {self._all_target_states}')
            return False
        elif prev_state not in self._all_source_states:
            raise exceptions.UnauthorizedOperation(
                action=self._name,
                message=f'This transition is not possible, {prev_state} cannot go to {self._all_target_states}. If there is a sharing or revoking in progress wait until it is complete and try again.',
            )
        else:
            return True

    def get_transition_target(self, prev_state):
        if self.validate_transition(prev_state):
            for target_state, list_prev_states in self._transitions.items():
                if prev_state in list_prev_states:
                    return target_state
                else:
                    pass
        else:
            return prev_state


class ShareObjectSM:
    def __init__(self, state):
        self._state = state
        self.transitionTable = {
            ShareObjectActions.Submit.value: Transition(
                name=ShareObjectActions.Submit.value,
                transitions={
                    ShareObjectStatus.Submitted.value: [
                        ShareObjectStatus.Draft.value,
                        ShareObjectStatus.Rejected.value
                    ]
                }
            ),
            ShareObjectActions.Approve.value: Transition(
                name=ShareObjectActions.Approve.value,
                transitions={
                    ShareObjectStatus.Approved.value: [
                        ShareObjectStatus.Submitted.value
                    ]
                }
            ),
            ShareObjectActions.Reject.value: Transition(
                name=ShareObjectActions.Reject.value,
                transitions={
                    ShareObjectStatus.Rejected.value: [
                        ShareObjectStatus.Submitted.value
                    ]
                }
            ),
            ShareObjectActions.RevokeItems.value: Transition(
                name=ShareObjectActions.RevokeItems.value,
                transitions={
                    ShareObjectStatus.Revoked.value: [
                        ShareObjectStatus.Draft.value,
                        ShareObjectStatus.Submitted.value,
                        ShareObjectStatus.Rejected.value,
                        ShareObjectStatus.Processed.value
                    ]
                }
            ),
            ShareObjectActions.Start.value: Transition(
                name=ShareObjectActions.Start.value,
                transitions={
                    ShareObjectStatus.Share_In_Progress.value: [
                        ShareObjectStatus.Approved.value
                    ],
                    ShareObjectStatus.Revoke_In_Progress.value: [
                        ShareObjectStatus.Revoked.value
                    ]
                }
            ),
            ShareObjectActions.Finish.value: Transition(
                name=ShareObjectActions.Finish.value,
                transitions={
                    ShareObjectStatus.Processed.value: [
                        ShareObjectStatus.Share_In_Progress.value,
                        ShareObjectStatus.Revoke_In_Progress.value
                    ],
                }
            ),
            ShareObjectActions.FinishPending.value: Transition(
                name=ShareObjectActions.FinishPending.value,
                transitions={
                    ShareObjectStatus.Draft.value: [
                        ShareObjectStatus.Revoke_In_Progress.value,
                    ],
                }
            ),
            ShareObjectActions.Delete.value: Transition(
                name=ShareObjectActions.Delete.value,
                transitions={
                    ShareObjectStatus.Deleted.value: [
                        ShareObjectStatus.Rejected.value,
                        ShareObjectStatus.Draft.value,
                        ShareObjectStatus.Submitted.value,
                        ShareObjectStatus.Processed.value
                    ]
                }
            ),
            ShareItemActions.AddItem.value: Transition(
                name=ShareItemActions.AddItem.value,
                transitions={
                    ShareObjectStatus.Draft.value: [
                        ShareObjectStatus.Submitted.value,
                        ShareObjectStatus.Rejected.value,
                        ShareObjectStatus.Processed.value
                    ]
                }
            ),
        }

    def run_transition(self, transition):
        trans = self.transitionTable[transition]
        new_state = trans.get_transition_target(self._state)
        return new_state

    def update_state(self, session, share, new_state):
        logger.info(f"Updating share object {share.shareUri} in DB from {self._state} to state {new_state}")
        ShareObject.update_share_object_status(
            session=session,
            shareUri=share.shareUri,
            status=new_state
        )
        self._state = new_state
        return True

    @staticmethod
    def get_share_object_refreshable_states():
        return [
            ShareObjectStatus.Approved.value,
            ShareObjectStatus.Revoked.value
        ]


class ShareItemSM:
    def __init__(self, state):
        self._state = state
        self.transitionTable = {
            ShareItemActions.AddItem.value: Transition(
                name=ShareItemActions.AddItem.value,
                transitions={
                    ShareItemStatus.PendingApproval.value: [ShareItemStatus.Deleted.value]
                }
            ),
            ShareObjectActions.Submit.value: Transition(
                name=ShareObjectActions.Submit.value,
                transitions={
                    ShareItemStatus.PendingApproval.value: [
                        ShareItemStatus.Share_Rejected.value,
                        ShareItemStatus.Share_Failed.value
                    ],
                    ShareItemStatus.Revoke_Approved.value: [ShareItemStatus.Revoke_Approved.value],
                    ShareItemStatus.Revoke_Failed.value: [ShareItemStatus.Revoke_Failed.value],
                    ShareItemStatus.Share_Approved.value: [ShareItemStatus.Share_Approved.value],
                    ShareItemStatus.Share_Succeeded.value: [ShareItemStatus.Share_Succeeded.value],
                    ShareItemStatus.Revoke_Succeeded.value: [ShareItemStatus.Revoke_Succeeded.value],
                    ShareItemStatus.Share_In_Progress.value: [ShareItemStatus.Share_In_Progress.value],
                    ShareItemStatus.Revoke_In_Progress.value: [ShareItemStatus.Revoke_In_Progress.value],
                }
            ),
            ShareObjectActions.Approve.value: Transition(
                name=ShareObjectActions.Approve.value,
                transitions={
                    ShareItemStatus.Share_Approved.value: [ShareItemStatus.PendingApproval.value],
                    ShareItemStatus.Revoke_Approved.value: [ShareItemStatus.Revoke_Approved.value],
                    ShareItemStatus.Revoke_Failed.value: [ShareItemStatus.Revoke_Failed.value],
                    ShareItemStatus.Share_Succeeded.value: [ShareItemStatus.Share_Succeeded.value],
                    ShareItemStatus.Revoke_Succeeded.value: [ShareItemStatus.Revoke_Succeeded.value],
                    ShareItemStatus.Share_In_Progress.value: [ShareItemStatus.Share_In_Progress.value],
                    ShareItemStatus.Revoke_In_Progress.value: [ShareItemStatus.Revoke_In_Progress.value],
                }
            ),
            ShareObjectActions.Reject.value: Transition(
                name=ShareObjectActions.Reject.value,
                transitions={
                    ShareItemStatus.Share_Rejected.value: [ShareItemStatus.PendingApproval.value],
                    ShareItemStatus.Revoke_Approved.value: [ShareItemStatus.Revoke_Approved.value],
                    ShareItemStatus.Revoke_Failed.value: [ShareItemStatus.Revoke_Failed.value],
                    ShareItemStatus.Share_Succeeded.value: [ShareItemStatus.Share_Succeeded.value],
                    ShareItemStatus.Revoke_Succeeded.value: [ShareItemStatus.Revoke_Succeeded.value],
                    ShareItemStatus.Share_In_Progress.value: [ShareItemStatus.Share_In_Progress.value],
                    ShareItemStatus.Revoke_In_Progress.value: [ShareItemStatus.Revoke_In_Progress.value],
                }
            ),
            ShareObjectActions.Start.value: Transition(
                name=ShareObjectActions.Start.value,
                transitions={
                    ShareItemStatus.Share_In_Progress.value: [ShareItemStatus.Share_Approved.value],
                    ShareItemStatus.Revoke_In_Progress.value: [ShareItemStatus.Revoke_Approved.value],
                }
            ),
            ShareItemActions.Success.value: Transition(
                name=ShareItemActions.Success.value,
                transitions={
                    ShareItemStatus.Share_Succeeded.value: [ShareItemStatus.Share_In_Progress.value],
                    ShareItemStatus.Revoke_Succeeded.value: [ShareItemStatus.Revoke_In_Progress.value],
                }
            ),
            ShareItemActions.Failure.value: Transition(
                name=ShareItemActions.Failure.value,
                transitions={
                    ShareItemStatus.Share_Failed.value: [ShareItemStatus.Share_In_Progress.value],
                    ShareItemStatus.Revoke_Failed.value: [ShareItemStatus.Revoke_In_Progress.value],
                }
            ),
            ShareItemActions.RemoveItem.value: Transition(
                name=ShareItemActions.RemoveItem.value,
                transitions={
                    ShareItemStatus.Deleted.value: [
                        ShareItemStatus.PendingApproval.value,
                        ShareItemStatus.Share_Rejected.value,
                        ShareItemStatus.Share_Failed.value,
                        ShareItemStatus.Revoke_Succeeded.value
                    ]
                }
            ),
            ShareObjectActions.RevokeItems.value: Transition(
                name=ShareObjectActions.RevokeItems.value,
                transitions={
                    ShareItemStatus.Revoke_Approved.value: [
                        ShareItemStatus.Share_Succeeded.value,
                        ShareItemStatus.Revoke_Failed.value,
                        ShareItemStatus.Revoke_Approved.value
                    ]
                }
            ),
            ShareObjectActions.Delete.value: Transition(
                name=ShareObjectActions.Delete.value,
                transitions={
                    ShareItemStatus.Deleted.value: [
                        ShareItemStatus.PendingApproval.value,
                        ShareItemStatus.Share_Rejected.value,
                        ShareItemStatus.Share_Failed.value,
                        ShareItemStatus.Revoke_Succeeded.value
                    ]
                }
            )
        }

    def run_transition(self, transition):
        trans = self.transitionTable[transition]
        new_state = trans.get_transition_target(self._state)
        return new_state

    def update_state(self, session, share_uri, new_state):
        if share_uri and (new_state != self._state):
            if new_state == ShareItemStatus.Deleted.value:
                logger.info(f"Deleting share items in DB in {self._state} state")
                ShareObject.delete_share_item_status_batch(
                    session=session,
                    share_uri=share_uri,
                    status=self._state
                )
            else:
                logger.info(f"Updating share items in DB from {self._state} to state {new_state}")
                ShareObject.update_share_item_status_batch(
                    session=session,
                    share_uri=share_uri,
                    old_status=self._state,
                    new_status=new_state
                )
            self._state = new_state
        else:
            logger.info(f"Share Items in DB already in target state {new_state} or no update is required")
            return True

    def update_state_single_item(self, session, share_item, new_state):
        logger.info(f"Updating share item in DB {share_item.shareItemUri} status to {new_state}")
        ShareObject.update_share_item_status(
            session=session,
            uri=share_item.shareItemUri,
            status=new_state
        )
        self._state = new_state
        return True

    @staticmethod
    def get_share_item_shared_states():
        return [
            ShareItemStatus.Share_Succeeded.value,
            ShareItemStatus.Share_In_Progress.value,
            ShareItemStatus.Revoke_Failed.value,
            ShareItemStatus.Revoke_In_Progress.value,
            ShareItemStatus.Revoke_Approved.value
        ]

    @staticmethod
    def get_share_item_revokable_states():
        return [
            ShareItemStatus.Share_Succeeded.value,
            ShareItemStatus.Revoke_Failed.value,
        ]


class ShareObject:
    @staticmethod
    @has_resource_perm(permissions.CREATE_SHARE_OBJECT)
    def create_share_object(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.ShareObject:
        if not data:
            raise exceptions.RequiredParameter(data)
        if not data.get('principalId'):
            raise exceptions.RequiredParameter('principalId')
        if not data.get('datasetUri'):
            raise exceptions.RequiredParameter('datasetUri')

        principalId = data['principalId']
        principalType = data['principalType']
        datasetUri = data['datasetUri']
        environmentUri = uri
        groupUri = data['groupUri']
        itemUri = data.get('itemUri')
        itemType = data.get('itemType')

        dataset: models.Dataset = data.get(
            'dataset', api.Dataset.get_dataset_by_uri(session, datasetUri)
        )
        environment: models.Environment = data.get(
            'environment',
            api.Environment.get_environment_by_uri(session, environmentUri),
        )

        if environment.region != dataset.region:
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_SHARE_OBJECT,
                message=f'Requester Team {groupUri} works in region {environment.region} and the requested dataset is stored in region {dataset.region}',
            )

        if principalType == models.PrincipalType.ConsumptionRole.value:
            consumption_role: models.ConsumptionRole = api.Environment.get_environment_consumption_role(
                session,
                principalId,
                environmentUri
            )
            principalIAMRoleName = consumption_role.IAMRoleName
        else:
            env_group: models.EnvironmentGroup = api.Environment.get_environment_group(
                session,
                groupUri,
                environmentUri
            )
            principalIAMRoleName = env_group.environmentIAMRoleName

        if (
            dataset.stewards == groupUri or dataset.SamlAdminGroupName == groupUri
        ) and environment.environmentUri == dataset.environmentUri and principalType == models.PrincipalType.Group.value:
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_SHARE_OBJECT,
                message=f'Team: {groupUri} is managing the dataset {dataset.name}',
            )

        ShareObject.validate_group_membership(
            session=session,
            username=username,
            groups=groups,
            share_object_group=groupUri,
            environment_uri=uri,
        )

        share: models.ShareObject = (
            session.query(models.ShareObject)
            .filter(
                and_(
                    models.ShareObject.datasetUri == datasetUri,
                    models.ShareObject.principalId == principalId,
                    models.ShareObject.environmentUri == environmentUri,
                    models.ShareObject.groupUri == groupUri,
                )
            )
            .first()
        )
        if not share:
            share = models.ShareObject(
                datasetUri=dataset.datasetUri,
                environmentUri=environment.environmentUri,
                owner=username,
                groupUri=groupUri,
                principalId=principalId,
                principalType=principalType,
                principalIAMRoleName=principalIAMRoleName,
                status=ShareObjectStatus.Draft.value,
            )
            session.add(share)
            session.commit()

        if itemUri:
            item = None
            if itemType:
                if itemType == ShareableType.StorageLocation.value:
                    item = session.query(models.DatasetStorageLocation).get(itemUri)
                if itemType == ShareableType.Table.value:
                    item = session.query(models.DatasetTable).get(itemUri)

            share_item = (
                session.query(models.ShareObjectItem)
                .filter(
                    and_(
                        models.ShareObjectItem.shareUri == share.shareUri,
                        models.ShareObjectItem.itemUri == itemUri,
                    )
                )
                .first()
            )
            S3AccessPointName = utils.slugify(
                share.datasetUri + '-' + share.principalId,
                max_length=50, lowercase=True, regex_pattern='[^a-zA-Z0-9-]', separator='-'
            )

            if not share_item and item:
                new_share_item: models.ShareObjectItem = models.ShareObjectItem(
                    shareUri=share.shareUri,
                    itemUri=itemUri,
                    itemType=itemType,
                    itemName=item.name,
                    status=ShareItemStatus.PendingApproval.value,
                    owner=username,
                    GlueDatabaseName=dataset.GlueDatabaseName
                    if itemType == ShareableType.Table.value
                    else '',
                    GlueTableName=item.GlueTableName
                    if itemType == ShareableType.Table.value
                    else '',
                    S3AccessPointName=S3AccessPointName
                    if itemType == ShareableType.StorageLocation.value
                    else '',
                )
                session.add(new_share_item)

        activity = models.Activity(
            action='SHARE_OBJECT:CREATE',
            label='SHARE_OBJECT:CREATE',
            owner=username,
            summary=f'{username} created a share object for the {dataset.name} in {environment.name} for the principal: {principalId}',
            targetUri=dataset.datasetUri,
            targetType='dataset',
        )
        session.add(activity)

        # Attaching REQUESTER permissions to:
        # requester group (groupUri)
        # dataset.SamlAdminGroupName
        # environment.SamlGroupName
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=groupUri,
            permissions=permissions.SHARE_OBJECT_REQUESTER,
            resource_uri=share.shareUri,
            resource_type=models.ShareObject.__name__,
        )
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=dataset.SamlAdminGroupName,
            permissions=permissions.SHARE_OBJECT_REQUESTER,
            resource_uri=share.shareUri,
            resource_type=models.ShareObject.__name__,
        )
        if dataset.SamlAdminGroupName != environment.SamlGroupName:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=environment.SamlGroupName,
                permissions=permissions.SHARE_OBJECT_REQUESTER,
                resource_uri=share.shareUri,
                resource_type=models.ShareObject.__name__,
            )
        # Attaching REQUESTER permissions to:
        # dataset.stewards (includes the dataset Admins)
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=dataset.stewards,
            permissions=permissions.SHARE_OBJECT_APPROVER,
            resource_uri=share.shareUri,
            resource_type=models.ShareObject.__name__,
        )
        return share

    @staticmethod
    def validate_group_membership(
        session, environment_uri, share_object_group, username, groups
    ):
        if share_object_group and share_object_group not in groups:
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_SHARE_OBJECT,
                message=f'User: {username} is not a member of the team {share_object_group}',
            )
        if share_object_group not in Environment.list_environment_groups(
            session=session,
            username=username,
            groups=groups,
            uri=environment_uri,
            data=None,
            check_perm=True,
        ):
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_SHARE_OBJECT,
                message=f'Team: {share_object_group} is not a member of the environment {environment_uri}',
            )

    @staticmethod
    @has_resource_perm(permissions.SUBMIT_SHARE_OBJECT)
    def submit_share_object(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.ShareObject:
        share = ShareObject.get_share_by_uri(session, uri)
        dataset = api.Dataset.get_dataset_by_uri(session, share.datasetUri)
        share_items_states = ShareObject.get_share_items_states(session, uri)

        valid_states = [ShareItemStatus.PendingApproval.value]
        valid_share_items_states = [x for x in valid_states if x in share_items_states]

        if valid_share_items_states == []:
            raise exceptions.ShareItemsFound(
                action='Submit Share Object',
                message='The request is empty of pending items. Add items to share request.',
            )

        Share_SM = ShareObjectSM(share.status)
        new_share_state = Share_SM.run_transition(ShareObjectActions.Submit.value)

        for item_state in share_items_states:
            Item_SM = ShareItemSM(item_state)
            new_state = Item_SM.run_transition(ShareObjectActions.Submit.value)
            Item_SM.update_state(session, share.shareUri, new_state)

        Share_SM.update_state(session, share, new_share_state)

        api.Notification.notify_share_object_submission(
            session, username, dataset, share
        )
        return share

    @staticmethod
    @has_resource_perm(permissions.APPROVE_SHARE_OBJECT)
    def approve_share_object(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.ShareObject:
        share = ShareObject.get_share_by_uri(session, uri)
        dataset = api.Dataset.get_dataset_by_uri(session, share.datasetUri)
        share_items_states = ShareObject.get_share_items_states(session, uri)

        Share_SM = ShareObjectSM(share.status)
        new_share_state = Share_SM.run_transition(ShareObjectActions.Approve.value)

        for item_state in share_items_states:
            Item_SM = ShareItemSM(item_state)
            new_state = Item_SM.run_transition(ShareObjectActions.Approve.value)
            Item_SM.update_state(session, share.shareUri, new_state)

        Share_SM.update_state(session, share, new_share_state)

        # GET TABLES SHARED AND APPROVE SHARE FOR EACH TABLE
        share_table_items = session.query(models.ShareObjectItem).filter(
            (
                and_(
                    models.ShareObjectItem.shareUri == uri,
                    models.ShareObjectItem.itemType == ShareableType.Table.value
                )
            )
        ).all()
        for table in share_table_items:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=share.principalId,
                permissions=permissions.DATASET_TABLE_READ,
                resource_uri=table.itemUri,
                resource_type=models.DatasetTable.__name__,
            )

        api.Notification.notify_share_object_approval(session, username, dataset, share)
        return share

    @staticmethod
    @has_resource_perm(permissions.REJECT_SHARE_OBJECT)
    def reject_share_object(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.ShareObject:

        share = ShareObject.get_share_by_uri(session, uri)
        dataset = api.Dataset.get_dataset_by_uri(session, share.datasetUri)
        share_items_states = ShareObject.get_share_items_states(session, uri)

        Share_SM = ShareObjectSM(share.status)
        new_share_state = Share_SM.run_transition(ShareObjectActions.Reject.value)

        for item_state in share_items_states:
            Item_SM = ShareItemSM(item_state)
            new_state = Item_SM.run_transition(ShareObjectActions.Reject.value)
            Item_SM.update_state(session, share.shareUri, new_state)

        Share_SM.update_state(session, share, new_share_state)

        ResourcePolicy.delete_resource_policy(
            session=session,
            group=share.groupUri,
            resource_uri=dataset.datasetUri,
        )
        api.Notification.notify_share_object_rejection(session, username, dataset, share)
        return share

    @staticmethod
    @has_resource_perm(permissions.GET_SHARE_OBJECT)
    def revoke_items_share_object(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.ShareObject:

        share = ShareObject.get_share_by_uri(session, uri)
        dataset = api.Dataset.get_dataset_by_uri(session, share.datasetUri)
        revoked_items_states = ShareObject.get_share_items_states(session, uri, data.get("revokedItemUris"))
        revoked_items = [ShareObject.get_share_item_by_uri(session, uri) for uri in data.get("revokedItemUris")]

        if revoked_items_states == []:
            raise exceptions.ShareItemsFound(
                action='Revoke Items from Share Object',
                message='Nothing to be revoked.',
            )

        Share_SM = ShareObjectSM(share.status)
        new_share_state = Share_SM.run_transition(ShareObjectActions.RevokeItems.value)

        for item_state in revoked_items_states:
            Item_SM = ShareItemSM(item_state)
            new_state = Item_SM.run_transition(ShareObjectActions.RevokeItems.value)
            for item in revoked_items:
                if item.status == item_state:
                    Item_SM.update_state_single_item(session, item, new_state)

        Share_SM.update_state(session, share, new_share_state)

        ResourcePolicy.delete_resource_policy(
            session=session,
            group=share.groupUri,
            resource_uri=dataset.datasetUri,
        )
        api.Notification.notify_share_object_rejection(session, username, dataset, share)
        return share

    @staticmethod
    @has_resource_perm(permissions.GET_SHARE_OBJECT)
    def get_share_object(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ):
        share = session.query(models.ShareObject).get(uri)
        if not share:
            raise exceptions.ObjectNotFound('Share', uri)

        return share

    @staticmethod
    @has_resource_perm(permissions.GET_SHARE_OBJECT)
    def get_share_item(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ):
        share_item: models.ShareObjectItem = data.get(
            'share_item',
            ShareObject.get_share_item_by_uri(session, data['shareItemUri']),
        )
        if share_item.itemType == ShareableType.Table.value:
            return session.query(models.DatasetTable).get(share_item.itemUri)
        if share_item.itemType == ShareableType.StorageLocation:
            return session.Query(models.DatasetStorageLocation).get(share_item.itemUri)

    @staticmethod
    def get_share_by_uri(session, uri):
        share = session.query(models.ShareObject).get(uri)
        if not share:
            raise exceptions.ObjectNotFound('Share', uri)
        return share

    @staticmethod
    def get_share_by_dataset_attributes(session, dataset_uri, dataset_owner):
        share: models.ShareObject = (
            session.query(models.ShareObject)
            .filter(models.ShareObject.datasetUri == dataset_uri)
            .filter(models.ShareObject.owner == dataset_owner)
            .first()
        )
        return share

    @staticmethod
    @has_resource_perm(permissions.ADD_ITEM)
    def add_share_object_item(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.ShareObjectItem:
        itemType = data.get('itemType')
        itemUri = data.get('itemUri')
        item = None
        share: models.ShareObject = session.query(models.ShareObject).get(uri)
        dataset: models.Dataset = session.query(models.Dataset).get(share.datasetUri)
        target_environment: models.Environment = session.query(models.Environment).get(
            share.environmentUri
        )

        Share_SM = ShareObjectSM(share.status)
        new_share_state = Share_SM.run_transition(ShareItemActions.AddItem.value)
        Share_SM.update_state(session, share, new_share_state)

        if itemType == ShareableType.Table.value:
            item: models.DatasetTable = session.query(models.DatasetTable).get(itemUri)
            if item and item.region != target_environment.region:
                raise exceptions.UnauthorizedOperation(
                    action=permissions.ADD_ITEM,
                    message=f'Lake Formation cross region sharing is not supported. '
                    f'Table {item.GlueTableName} is in {item.region} and target environment '
                    f'{target_environment.name} is in {target_environment.region} ',
                )

        elif itemType == ShareableType.StorageLocation.value:
            item = session.query(models.DatasetStorageLocation).get(itemUri)

        if not item:
            raise exceptions.ObjectNotFound('ShareObjectItem', itemUri)

        shareItem: models.ShareObjectItem = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.shareUri == uri,
                    models.ShareObjectItem.itemUri == itemUri,
                )
            )
            .first()
        )
        S3AccessPointName = utils.slugify(
            share.datasetUri + '-' + share.principalId,
            max_length=50, lowercase=True, regex_pattern='[^a-zA-Z0-9-]', separator='-'
        )
        logger.info(f"S3AccessPointName={S3AccessPointName}")

        if not shareItem:
            shareItem = models.ShareObjectItem(
                shareUri=uri,
                itemUri=itemUri,
                itemType=itemType,
                itemName=item.name,
                status=ShareItemStatus.PendingApproval.value,
                owner=username,
                GlueDatabaseName=dataset.GlueDatabaseName
                if itemType == ShareableType.Table.value
                else '',
                GlueTableName=item.GlueTableName
                if itemType == ShareableType.Table.value
                else '',
                S3AccessPointName=S3AccessPointName
                if itemType == ShareableType.StorageLocation.value
                else '',
            )
            session.add(shareItem)

        return shareItem

    @staticmethod
    @has_resource_perm(permissions.REMOVE_ITEM)
    def remove_share_object_item(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> bool:

        share_item: models.ShareObjectItem = data.get(
            'share_item',
            ShareObject.get_share_item_by_uri(session, data['shareItemUri']),
        )
        share: models.ShareObject = data.get(
            'share',
            ShareObject.get_share_by_uri(session, uri),
        )

        Item_SM = ShareItemSM(share_item.status)
        newstatus = Item_SM.run_transition(ShareItemActions.RemoveItem.value)

        session.delete(share_item)
        return True

    @staticmethod
    @has_resource_perm(permissions.DELETE_SHARE_OBJECT)
    def delete_share_object(session, username, groups, uri, data=None, check_perm=None):
        share: models.ShareObject = ShareObject.get_share_by_uri(session, uri)
        share_items_states = ShareObject.get_share_items_states(session, uri)
        shared_share_items_states = [x for x in ShareItemSM.get_share_item_shared_states() if x in share_items_states]

        Share_SM = ShareObjectSM(share.status)
        new_share_state = Share_SM.run_transition(ShareObjectActions.Delete.value)

        for item_state in share_items_states:
            Item_SM = ShareItemSM(item_state)
            new_state = Item_SM.run_transition(ShareObjectActions.Delete.value)
            Item_SM.update_state(session, share.shareUri, new_state)

        if shared_share_items_states:
            raise exceptions.ShareItemsFound(
                action='Delete share object',
                message='There are shared items in this request. Revoke access to these items before deleting the request.',
            )
        if new_share_state == ShareObjectStatus.Deleted.value:
            session.delete(share)

        return True

    @staticmethod
    def check_existing_shared_items(session, uri):
        share: models.ShareObject = ShareObject.get_share_by_uri(session, uri)
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        shared_items = session.query(models.ShareObjectItem).filter(
            and_(
                models.ShareObjectItem.shareUri == share.shareUri,
                models.ShareObjectItem.status.in_(share_item_shared_states)
            )
        ).all()
        if shared_items:
            return True
        return False

    @staticmethod
    def check_existing_shared_items_of_type(session, uri, item_type):
        share: models.ShareObject = ShareObject.get_share_by_uri(session, uri)
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        shared_items = session.query(models.ShareObjectItem).filter(
            and_(
                models.ShareObjectItem.shareUri == share.shareUri,
                models.ShareObjectItem.itemType == item_type,
                models.ShareObjectItem.status.in_(share_item_shared_states)
            )
        ).all()
        if shared_items:
            return True
        return False

    @staticmethod
    def check_pending_share_items(session, uri):
        share: models.ShareObject = ShareObject.get_share_by_uri(session, uri)
        shared_items = session.query(models.ShareObjectItem).filter(
            and_(
                models.ShareObjectItem.shareUri == share.shareUri,
                models.ShareObjectItem.status.in_([ShareItemStatus.PendingApproval.value])
            )
        ).all()
        if shared_items:
            return True
        return False

    @staticmethod
    def get_share_item_by_uri(session, uri):
        share_item: models.ShareObjectItem = session.query(models.ShareObjectItem).get(
            uri
        )
        if not share_item:
            raise exceptions.ObjectNotFound('ShareObjectItem', uri)

        return share_item

    @staticmethod
    @has_resource_perm(permissions.LIST_SHARED_ITEMS)
    def list_shared_items(session, username, groups, uri, data=None, check_perm=None):
        share: models.ShareObject = ShareObject.get_share_by_uri(session, uri)
        query = session.query(models.ShareObjectItem).filter(
            models.ShareObjectItem.shareUri == share.shareUri,
        )
        return paginate(
            query, page=data.get('page', 1), page_size=data.get('pageSize', 5)
        ).to_dict()

    @staticmethod
    def list_shareable_items(
        session, username, groups, uri, data=None, check_perm=None
    ):

        share: models.ShareObject = data.get(
            'share', ShareObject.get_share_by_uri(session, uri)
        )
        share_item_revokable_states = ShareItemSM.get_share_item_revokable_states()
        datasetUri = share.datasetUri

        # All tables from dataset with a column isShared
        # marking the table as part of the shareObject
        tables = (
            session.query(
                models.DatasetTable.tableUri.label('itemUri'),
                func.coalesce('DatasetTable').label('itemType'),
                models.DatasetTable.GlueTableName.label('itemName'),
                models.DatasetTable.description.label('description'),
                models.ShareObjectItem.shareItemUri.label('shareItemUri'),
                models.ShareObjectItem.status.label('status'),
                case(
                    [(models.ShareObjectItem.shareItemUri.isnot(None), True)],
                    else_=False,
                ).label('isShared'),
            )
            .outerjoin(
                models.ShareObjectItem,
                and_(
                    models.ShareObjectItem.shareUri == share.shareUri,
                    models.DatasetTable.tableUri == models.ShareObjectItem.itemUri,
                ),
            )
            .filter(models.DatasetTable.datasetUri == datasetUri)
        )
        if data:
            if data.get("isRevokable"):
                tables = tables.filter(models.ShareObjectItem.status.in_(share_item_revokable_states))

        # All folders from the dataset with a column isShared
        # marking the folder as part of the shareObject
        locations = (
            session.query(
                models.DatasetStorageLocation.locationUri.label('itemUri'),
                func.coalesce('DatasetStorageLocation').label('itemType'),
                models.DatasetStorageLocation.S3Prefix.label('itemName'),
                models.DatasetStorageLocation.description.label('description'),
                models.ShareObjectItem.shareItemUri.label('shareItemUri'),
                models.ShareObjectItem.status.label('status'),
                case(
                    [(models.ShareObjectItem.shareItemUri.isnot(None), True)],
                    else_=False,
                ).label('isShared'),
            )
            .outerjoin(
                models.ShareObjectItem,
                and_(
                    models.ShareObjectItem.shareUri == share.shareUri,
                    models.DatasetStorageLocation.locationUri
                    == models.ShareObjectItem.itemUri,
                ),
            )
            .filter(models.DatasetStorageLocation.datasetUri == datasetUri)
        )
        if data:
            if data.get("isRevokable"):
                locations = locations.filter(models.ShareObjectItem.status.in_(share_item_revokable_states))

        shareable_objects = tables.union(locations).subquery('shareable_objects')
        query = session.query(shareable_objects)

        if data:
            if data.get('term'):
                term = data.get('term')
                query = query.filter(
                    or_(
                        shareable_objects.c.itemName.ilike(term + '%'),
                        shareable_objects.c.description.ilike(term + '%'),
                    )
                )
            if 'isShared' in data.keys():
                isShared = data.get('isShared')
                query = query.filter(shareable_objects.c.isShared == isShared)

        return paginate(query, data.get('page', 1), data.get('pageSize', 10)).to_dict()

    @staticmethod
    def list_user_received_share_requests(
        session, username, groups, uri, data=None, check_perm=None
    ):
        query = (
            session.query(models.ShareObject)
            .join(
                models.Dataset,
                models.Dataset.datasetUri == models.ShareObject.datasetUri,
            )
            .filter(
                or_(
                    models.Dataset.businessOwnerEmail == username,
                    models.Dataset.businessOwnerDelegationEmails.contains(
                        f'{{{username}}}'
                    ),
                    models.Dataset.stewards.in_(groups),
                )
            )
        )
        return paginate(query, data.get('page', 1), data.get('pageSize', 10)).to_dict()

    @staticmethod
    def list_user_sent_share_requests(
        session, username, groups, uri, data=None, check_perm=None
    ):
        query = (
            session.query(models.ShareObject)
            .join(
                models.Environment,
                models.Environment.environmentUri == models.ShareObject.environmentUri,
            )
            .filter(
                or_(
                    models.ShareObject.owner == username,
                    and_(
                        models.ShareObject.groupUri.in_(groups),
                        models.ShareObject.principalType.in_([PrincipalType.Group.value, PrincipalType.ConsumptionRole.value])
                    ),
                )
            )
        )
        return paginate(query, data.get('page', 1), data.get('pageSize', 10)).to_dict()

    @staticmethod
    def get_share_by_dataset_and_environment(session, dataset_uri, environment_uri):
        environment_groups = session.query(models.EnvironmentGroup).filter(
            models.EnvironmentGroup.environmentUri == environment_uri
        )
        groups = [g.groupUri for g in environment_groups]
        share = session.query(models.ShareObject).filter(
            and_(
                models.ShareObject.datasetUri == dataset_uri,
                models.ShareObject.environmentUri == environment_uri,
                models.ShareObject.groupUri.in_(groups),
            )
        )
        if not share:
            raise exceptions.ObjectNotFound('Share', f'{dataset_uri}/{environment_uri}')
        return share

    @staticmethod
    def update_share_object_status(
            session,
            shareUri: str,
            status: str,
    ) -> models.ShareObject:

        share = ShareObject.get_share_by_uri(session, shareUri)
        share.status = status
        session.commit()
        return share

    @staticmethod
    def update_share_item_status(
        session,
        uri: str,
        status: str,
    ) -> models.ShareObjectItem:

        share_item = ShareObject.get_share_item_by_uri(session, uri)
        share_item.status = status
        session.commit()
        return share_item

    @staticmethod
    def delete_share_item_status_batch(
        session,
        share_uri: str,
        status: str,
    ):
        (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.shareUri == share_uri,
                    models.ShareObjectItem.status == status
                )
            )
            .delete()
        )

    @staticmethod
    def update_share_item_status_batch(
        session,
        share_uri: str,
        old_status: str,
        new_status: str,
    ) -> bool:

        (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.shareUri == share_uri,
                    models.ShareObjectItem.status == old_status
                )
            )
            .update(
                {
                    models.ShareObjectItem.status: new_status,
                }
            )
        )
        return True

    @staticmethod
    def find_share_item_by_table(
        session,
        share: models.ShareObject,
        table: models.DatasetTable,
    ) -> models.ShareObjectItem:
        share_item: models.ShareObjectItem = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.itemUri == table.tableUri,
                    models.ShareObjectItem.shareUri == share.shareUri,
                )
            )
            .first()
        )
        return share_item

    @staticmethod
    def find_share_item_by_folder(
        session,
        share: models.ShareObject,
        folder: models.DatasetStorageLocation,
    ) -> models.ShareObjectItem:
        share_item: models.ShareObjectItem = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.itemUri == folder.locationUri,
                    models.ShareObjectItem.shareUri == share.shareUri,
                )
            )
            .first()
        )
        return share_item

    @staticmethod
    def get_share_data(session, share_uri):
        share: models.ShareObject = session.query(models.ShareObject).get(share_uri)
        if not share:
            raise exceptions.ObjectNotFound('Share', share_uri)

        dataset: models.Dataset = session.query(models.Dataset).get(share.datasetUri)
        if not dataset:
            raise exceptions.ObjectNotFound('Dataset', share.datasetUri)

        source_environment: models.Environment = session.query(models.Environment).get(
            dataset.environmentUri
        )
        if not source_environment:
            raise exceptions.ObjectNotFound('SourceEnvironment', dataset.environmentUri)

        target_environment: models.Environment = session.query(models.Environment).get(
            share.environmentUri
        )
        if not target_environment:
            raise exceptions.ObjectNotFound('TargetEnvironment', share.environmentUri)

        env_group: models.EnvironmentGroup = (
            session.query(models.EnvironmentGroup)
            .filter(
                and_(
                    models.EnvironmentGroup.environmentUri == share.environmentUri,
                    models.EnvironmentGroup.groupUri == share.groupUri,
                )
            )
            .first()
        )
        if not env_group:
            raise Exception(
                f'Share object Team {share.groupUri} is not a member of the '
                f'environment {target_environment.name}/{target_environment.AwsAccountId}'
            )

        source_env_group: models.EnvironmentGroup = (
            session.query(models.EnvironmentGroup)
            .filter(
                and_(
                    models.EnvironmentGroup.environmentUri == dataset.environmentUri,
                    models.EnvironmentGroup.groupUri == dataset.SamlAdminGroupName,
                )
            )
            .first()
        )
        if not source_env_group:
            raise Exception(
                f'Share object Team {dataset.SamlAdminGroupName} is not a member of the '
                f'environment {dataset.environmentUri}'
            )

        return (
            source_env_group,
            env_group,
            dataset,
            share,
            source_environment,
            target_environment,
        )

    @staticmethod
    def get_share_data_items(session, share_uri, status):
        share: models.ShareObject = session.query(models.ShareObject).get(share_uri)
        if not share:
            raise exceptions.ObjectNotFound('Share', share_uri)

        tables = (
            session.query(models.DatasetTable)
            .join(
                models.ShareObjectItem,
                models.ShareObjectItem.itemUri == models.DatasetTable.tableUri,
            )
            .join(
                models.ShareObject,
                models.ShareObject.shareUri == models.ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    models.ShareObject.datasetUri == share.datasetUri,
                    models.ShareObject.environmentUri
                    == share.environmentUri,
                    models.ShareObject.shareUri == share_uri,
                    models.ShareObjectItem.status == status,
                )
            )
            .all()
        )

        folders = (
            session.query(models.DatasetStorageLocation)
            .join(
                models.ShareObjectItem,
                models.ShareObjectItem.itemUri == models.DatasetStorageLocation.locationUri,
            )
            .join(
                models.ShareObject,
                models.ShareObject.shareUri == models.ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    models.ShareObject.datasetUri == share.datasetUri,
                    models.ShareObject.environmentUri
                    == share.environmentUri,
                    models.ShareObject.shareUri == share_uri,
                    models.ShareObjectItem.status == status,
                )
            )
            .all()
        )

        return (
            tables,
            folders,
        )

    @staticmethod
    def other_approved_share_object_exists(session, environment_uri, dataset_uri):
        return (
            session.query(models.ShareObject)
            .filter(
                and_(
                    models.Environment.environmentUri == environment_uri,
                    models.ShareObject.status
                    == models.Enums.ShareObjectStatus.Approved.value,
                    models.ShareObject.datasetUri == dataset_uri,
                )
            )
            .all()
        )

    @staticmethod
    def get_share_items_states(session, share_uri, item_uris=None):
        query = (
            session.query(models.ShareObjectItem)
            .join(
                models.ShareObject,
                models.ShareObjectItem.shareUri == models.ShareObject.shareUri,
            )
            .filter(
                and_(
                    models.ShareObject.shareUri == share_uri,
                )
            )
        )
        if item_uris:
            query = query.filter(models.ShareObjectItem.shareItemUri.in_(item_uris))
        return [item.status for item in query.distinct(models.ShareObjectItem.status)]

    @staticmethod
    def resolve_share_object_statistics(session, uri, **kwargs):
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        tables = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.shareUri == uri,
                    models.ShareObjectItem.itemType == 'DatasetTable',
                )
            )
            .count()
        )
        locations = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.shareUri == uri,
                    models.ShareObjectItem.itemType == 'DatasetStorageLocation',
                )
            )
            .count()
        )
        shared_items = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.shareUri == uri,
                    models.ShareObjectItem.status.in_(share_item_shared_states),
                )
            )
            .count()
        )
        revoked_items = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.shareUri == uri,
                    models.ShareObjectItem.status.in_([ShareItemStatus.Revoke_Succeeded.value]),
                )
            )
            .count()
        )
        failed_states = [
            ShareItemStatus.Share_Failed.value,
            ShareItemStatus.Revoke_Failed.value
        ]
        failed_items = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.shareUri == uri,
                    models.ShareObjectItem.status.in_(failed_states),
                )
            )
            .count()
        )
        pending_states = [
            ShareItemStatus.PendingApproval.value
        ]
        pending_items = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.shareUri == uri,
                    models.ShareObjectItem.status.in_(pending_states),
                )
            )
            .count()
        )
        return {'tables': tables, 'locations': locations, 'sharedItems': shared_items, 'revokedItems': revoked_items, 'failedItems': failed_items, 'pendingItems': pending_items}
