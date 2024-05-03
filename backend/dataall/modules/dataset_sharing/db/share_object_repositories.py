import logging
from warnings import warn
from typing import List
from datetime import datetime

from sqlalchemy import and_, or_, func, case
from sqlalchemy.orm import Query

from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.core.organizations.db.organization_models import Organization
from dataall.base.db import exceptions, paginate
from dataall.modules.dataset_sharing.services.dataset_sharing_enums import (
    ShareItemHealthStatus,
    ShareObjectActions,
    ShareObjectStatus,
    ShareItemActions,
    ShareItemStatus,
    ShareableType,
    PrincipalType,
)
from dataall.modules.dataset_sharing.db.share_object_models import ShareObjectItem, ShareObject
from dataall.modules.datasets_base.db.dataset_repositories import DatasetRepository
from dataall.modules.datasets_base.db.dataset_models import DatasetStorageLocation, DatasetTable, Dataset, DatasetBucket

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
                message=f'This transition is not possible, {prev_state} cannot go to {self._all_target_states}. '
                f'If there is a sharing or revoking in progress wait until it is complete and try again.',
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
                    ShareObjectStatus.Submitted.value: [ShareObjectStatus.Draft.value, ShareObjectStatus.Rejected.value]
                },
            ),
            ShareObjectActions.Approve.value: Transition(
                name=ShareObjectActions.Approve.value,
                transitions={ShareObjectStatus.Approved.value: [ShareObjectStatus.Submitted.value]},
            ),
            ShareObjectActions.Reject.value: Transition(
                name=ShareObjectActions.Reject.value,
                transitions={ShareObjectStatus.Rejected.value: [ShareObjectStatus.Submitted.value]},
            ),
            ShareObjectActions.RevokeItems.value: Transition(
                name=ShareObjectActions.RevokeItems.value,
                transitions={
                    ShareObjectStatus.Revoked.value: [
                        ShareObjectStatus.Draft.value,
                        ShareObjectStatus.Submitted.value,
                        ShareObjectStatus.Rejected.value,
                        ShareObjectStatus.Processed.value,
                    ]
                },
            ),
            ShareObjectActions.Start.value: Transition(
                name=ShareObjectActions.Start.value,
                transitions={
                    ShareObjectStatus.Share_In_Progress.value: [ShareObjectStatus.Approved.value],
                    ShareObjectStatus.Revoke_In_Progress.value: [ShareObjectStatus.Revoked.value],
                },
            ),
            ShareObjectActions.Finish.value: Transition(
                name=ShareObjectActions.Finish.value,
                transitions={
                    ShareObjectStatus.Processed.value: [
                        ShareObjectStatus.Share_In_Progress.value,
                        ShareObjectStatus.Revoke_In_Progress.value,
                    ],
                },
            ),
            ShareObjectActions.FinishPending.value: Transition(
                name=ShareObjectActions.FinishPending.value,
                transitions={
                    ShareObjectStatus.Draft.value: [
                        ShareObjectStatus.Revoke_In_Progress.value,
                    ],
                },
            ),
            ShareObjectActions.Delete.value: Transition(
                name=ShareObjectActions.Delete.value,
                transitions={
                    ShareObjectStatus.Deleted.value: [
                        ShareObjectStatus.Rejected.value,
                        ShareObjectStatus.Draft.value,
                        ShareObjectStatus.Submitted.value,
                        ShareObjectStatus.Processed.value,
                    ]
                },
            ),
            ShareItemActions.AddItem.value: Transition(
                name=ShareItemActions.AddItem.value,
                transitions={
                    ShareObjectStatus.Draft.value: [
                        ShareObjectStatus.Submitted.value,
                        ShareObjectStatus.Rejected.value,
                        ShareObjectStatus.Processed.value,
                    ]
                },
            ),
            ShareObjectActions.AcquireLockFailure.value: Transition(
                name=ShareObjectActions.AcquireLockFailure.value,
                transitions={
                    ShareObjectStatus.Processed.value: [
                        ShareObjectStatus.Share_In_Progress.value,
                        ShareObjectStatus.Revoke_In_Progress.value,
                    ]
                },
            ),
        }

    def run_transition(self, transition):
        trans = self.transitionTable[transition]
        new_state = trans.get_transition_target(self._state)
        return new_state

    def update_state(self, session, share, new_state):
        logger.info(f'Updating share object {share.shareUri} in DB from {self._state} to state {new_state}')
        ShareObjectRepository.update_share_object_status(session=session, share_uri=share.shareUri, status=new_state)
        self._state = new_state
        return True


class ShareItemSM:
    def __init__(self, state):
        self._state = state
        self.transitionTable = {
            ShareItemActions.AddItem.value: Transition(
                name=ShareItemActions.AddItem.value,
                transitions={ShareItemStatus.PendingApproval.value: [ShareItemStatus.Deleted.value]},
            ),
            ShareObjectActions.Submit.value: Transition(
                name=ShareObjectActions.Submit.value,
                transitions={
                    ShareItemStatus.PendingApproval.value: [
                        ShareItemStatus.Share_Rejected.value,
                        ShareItemStatus.Share_Failed.value,
                    ],
                    ShareItemStatus.Revoke_Approved.value: [ShareItemStatus.Revoke_Approved.value],
                    ShareItemStatus.Revoke_Failed.value: [ShareItemStatus.Revoke_Failed.value],
                    ShareItemStatus.Share_Approved.value: [ShareItemStatus.Share_Approved.value],
                    ShareItemStatus.Share_Succeeded.value: [ShareItemStatus.Share_Succeeded.value],
                    ShareItemStatus.Revoke_Succeeded.value: [ShareItemStatus.Revoke_Succeeded.value],
                    ShareItemStatus.Share_In_Progress.value: [ShareItemStatus.Share_In_Progress.value],
                    ShareItemStatus.Revoke_In_Progress.value: [ShareItemStatus.Revoke_In_Progress.value],
                },
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
                },
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
                },
            ),
            ShareObjectActions.Start.value: Transition(
                name=ShareObjectActions.Start.value,
                transitions={
                    ShareItemStatus.Share_In_Progress.value: [ShareItemStatus.Share_Approved.value],
                    ShareItemStatus.Revoke_In_Progress.value: [ShareItemStatus.Revoke_Approved.value],
                },
            ),
            ShareItemActions.Success.value: Transition(
                name=ShareItemActions.Success.value,
                transitions={
                    ShareItemStatus.Share_Succeeded.value: [ShareItemStatus.Share_In_Progress.value],
                    ShareItemStatus.Revoke_Succeeded.value: [ShareItemStatus.Revoke_In_Progress.value],
                },
            ),
            ShareItemActions.Failure.value: Transition(
                name=ShareItemActions.Failure.value,
                transitions={
                    ShareItemStatus.Share_Failed.value: [ShareItemStatus.Share_In_Progress.value],
                    ShareItemStatus.Revoke_Failed.value: [ShareItemStatus.Revoke_In_Progress.value],
                },
            ),
            ShareItemActions.RemoveItem.value: Transition(
                name=ShareItemActions.RemoveItem.value,
                transitions={
                    ShareItemStatus.Deleted.value: [
                        ShareItemStatus.PendingApproval.value,
                        ShareItemStatus.Share_Rejected.value,
                        ShareItemStatus.Share_Failed.value,
                        ShareItemStatus.Revoke_Succeeded.value,
                    ]
                },
            ),
            ShareObjectActions.RevokeItems.value: Transition(
                name=ShareObjectActions.RevokeItems.value,
                transitions={
                    ShareItemStatus.Revoke_Approved.value: [
                        ShareItemStatus.Share_Succeeded.value,
                        ShareItemStatus.Revoke_Failed.value,
                        ShareItemStatus.Revoke_Approved.value,
                    ]
                },
            ),
            ShareObjectActions.Delete.value: Transition(
                name=ShareObjectActions.Delete.value,
                transitions={
                    ShareItemStatus.Deleted.value: [
                        ShareItemStatus.PendingApproval.value,
                        ShareItemStatus.Share_Rejected.value,
                        ShareItemStatus.Share_Failed.value,
                        ShareItemStatus.Revoke_Succeeded.value,
                    ]
                },
            ),
            ShareObjectActions.AcquireLockFailure.value: Transition(
                name=ShareObjectActions.AcquireLockFailure.value,
                transitions={
                    ShareItemStatus.Share_Failed.value: [ShareItemStatus.Share_Approved.value],
                    ShareItemStatus.Revoke_Failed.value: [ShareItemStatus.Revoke_Approved.value],
                },
            ),
        }

    def run_transition(self, transition):
        trans = self.transitionTable[transition]
        new_state = trans.get_transition_target(self._state)
        return new_state

    def update_state(self, session, share_uri, new_state):
        if share_uri and (new_state != self._state):
            if new_state == ShareItemStatus.Deleted.value:
                logger.info(f'Deleting share items in DB in {self._state} state')
                ShareObjectRepository.delete_share_item_status_batch(
                    session=session, share_uri=share_uri, status=self._state
                )
            else:
                logger.info(f'Updating share items in DB from {self._state} to state {new_state}')
                ShareObjectRepository.update_share_item_status_batch(
                    session=session, share_uri=share_uri, old_status=self._state, new_status=new_state
                )
            self._state = new_state
        else:
            logger.info(f'Share Items in DB already in target state {new_state} or no update is required')
            return True

    def update_state_single_item(self, session, share_item, new_state):
        logger.info(f'Updating share item in DB {share_item.shareItemUri} status to {new_state}')
        ShareObjectRepository.update_share_item_status(session=session, uri=share_item.shareItemUri, status=new_state)
        self._state = new_state
        return True

    @staticmethod
    def get_share_item_shared_states():
        return [
            ShareItemStatus.Share_Succeeded.value,
            ShareItemStatus.Share_In_Progress.value,
            ShareItemStatus.Revoke_Failed.value,
            ShareItemStatus.Revoke_In_Progress.value,
            ShareItemStatus.Revoke_Approved.value,
        ]

    @staticmethod
    def get_share_item_revokable_states():
        return [
            ShareItemStatus.Share_Succeeded.value,
            ShareItemStatus.Revoke_Failed.value,
        ]


class ShareEnvironmentResource(EnvironmentResource):
    @staticmethod
    def count_resources(session, environment, group_uri) -> int:
        return ShareObjectRepository.count_principal_shares(
            session, group_uri, environment.environmentUri, PrincipalType.Group
        )

    @staticmethod
    def count_role_resources(session, role_uri):
        return ShareObjectRepository.count_role_principal_shares(session, role_uri, PrincipalType.ConsumptionRole)

    @staticmethod
    def delete_env(session, environment):
        ShareObjectRepository.delete_all_share_items(session, environment.environmentUri)


class ShareObjectRepository:
    @staticmethod
    def save_and_commit(session, share):
        session.add(share)
        session.commit()

    @staticmethod
    def list_all_active_share_objects(session) -> [ShareObject]:
        return session.query(ShareObject).filter(ShareObject.deleted.is_(None)).all()

    @staticmethod
    def find_share(session, dataset: Dataset, env, principal_id, group_uri) -> ShareObject:
        return (
            session.query(ShareObject)
            .filter(
                and_(
                    ShareObject.datasetUri == dataset.datasetUri,
                    ShareObject.principalId == principal_id,
                    ShareObject.environmentUri == env.environmentUri,
                    ShareObject.groupUri == group_uri,
                )
            )
            .first()
        )

    @staticmethod
    def get_share_item(session, item_type, item_uri):
        if item_type == ShareableType.Table.value:
            return session.query(DatasetTable).get(item_uri)
        if item_type == ShareableType.StorageLocation.value:
            return session.query(DatasetStorageLocation).get(item_uri)
        if item_type == ShareableType.S3Bucket.value:
            return session.query(DatasetBucket).get(item_uri)

    @staticmethod
    def get_share_by_uri(session, uri):
        share = session.query(ShareObject).get(uri)
        if not share:
            raise exceptions.ObjectNotFound('Share', uri)
        return share

    @staticmethod
    def get_share_by_dataset_attributes(session, dataset_uri, dataset_owner):
        share: ShareObject = (
            session.query(ShareObject)
            .filter(ShareObject.datasetUri == dataset_uri)
            .filter(ShareObject.owner == dataset_owner)
            .first()
        )
        return share

    @staticmethod
    def remove_share_object_item(session, share_item):
        session.delete(share_item)
        return True

    @staticmethod
    def check_existing_shared_items(session, uri):
        share: ShareObject = ShareObjectRepository.get_share_by_uri(session, uri)
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        shared_items = (
            session.query(ShareObjectItem)
            .filter(
                and_(ShareObjectItem.shareUri == share.shareUri, ShareObjectItem.status.in_(share_item_shared_states))
            )
            .all()
        )
        if shared_items:
            return True
        return False

    @staticmethod
    def count_sharable_items(session, uri, share_type):
        return (
            session.query(ShareObjectItem)
            .filter(
                and_(
                    ShareObjectItem.shareUri == uri,
                    ShareObjectItem.itemType == share_type,
                )
            )
            .count()
        )

    @staticmethod
    def find_sharable_item(session, share_uri, item_uri) -> ShareObjectItem:
        return (
            session.query(ShareObjectItem)
            .filter(
                and_(
                    ShareObjectItem.itemUri == item_uri,
                    ShareObjectItem.shareUri == share_uri,
                )
            )
            .first()
        )

    @staticmethod
    def count_items_in_states(session, uri, states):
        return (
            session.query(ShareObjectItem)
            .filter(
                and_(
                    ShareObjectItem.shareUri == uri,
                    ShareObjectItem.status.in_(states),
                )
            )
            .count()
        )

    @staticmethod
    def check_existing_shared_items_of_type(session, uri, item_type):
        share: ShareObject = ShareObjectRepository.get_share_by_uri(session, uri)
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        shared_items = (
            session.query(ShareObjectItem)
            .filter(
                and_(
                    ShareObjectItem.shareUri == share.shareUri,
                    ShareObjectItem.itemType == item_type,
                    ShareObjectItem.status.in_(share_item_shared_states),
                )
            )
            .all()
        )
        if shared_items:
            return True
        return False

    @staticmethod
    def check_pending_share_items(session, uri):
        share: ShareObject = ShareObjectRepository.get_share_by_uri(session, uri)
        shared_items = (
            session.query(ShareObjectItem)
            .filter(
                and_(
                    ShareObjectItem.shareUri == share.shareUri,
                    ShareObjectItem.status.in_([ShareItemStatus.PendingApproval.value]),
                )
            )
            .all()
        )
        if shared_items:
            return True
        return False

    @staticmethod
    def get_share_item_by_uri(session, uri):
        share_item: ShareObjectItem = session.query(ShareObjectItem).get(uri)
        if not share_item:
            raise exceptions.ObjectNotFound('ShareObjectItem', uri)

        return share_item

    @staticmethod
    def list_shareable_items(session, share, states, data):
        # All tables from dataset with a column isShared
        # marking the table as part of the shareObject
        tables = (
            session.query(
                DatasetTable.tableUri.label('itemUri'),
                func.coalesce('DatasetTable').label('itemType'),
                DatasetTable.GlueTableName.label('itemName'),
                DatasetTable.description.label('description'),
                ShareObjectItem.shareItemUri.label('shareItemUri'),
                ShareObjectItem.status.label('status'),
                ShareObjectItem.healthStatus.label('healthStatus'),
                ShareObjectItem.healthMessage.label('healthMessage'),
                ShareObjectItem.lastVerificationTime.label('lastVerificationTime'),
                case(
                    [(ShareObjectItem.shareItemUri.isnot(None), True)],
                    else_=False,
                ).label('isShared'),
            )
            .outerjoin(
                ShareObjectItem,
                and_(
                    ShareObjectItem.shareUri == share.shareUri,
                    DatasetTable.tableUri == ShareObjectItem.itemUri,
                ),
            )
            .filter(DatasetTable.datasetUri == share.datasetUri)
        )
        if states:
            tables = tables.filter(ShareObjectItem.status.in_(states))

        # All folders from the dataset with a column isShared
        # marking the folder as part of the shareObject
        locations = (
            session.query(
                DatasetStorageLocation.locationUri.label('itemUri'),
                func.coalesce('DatasetStorageLocation').label('itemType'),
                DatasetStorageLocation.S3Prefix.label('itemName'),
                DatasetStorageLocation.description.label('description'),
                ShareObjectItem.shareItemUri.label('shareItemUri'),
                ShareObjectItem.status.label('status'),
                ShareObjectItem.healthStatus.label('healthStatus'),
                ShareObjectItem.healthMessage.label('healthMessage'),
                ShareObjectItem.lastVerificationTime.label('lastVerificationTime'),
                case(
                    [(ShareObjectItem.shareItemUri.isnot(None), True)],
                    else_=False,
                ).label('isShared'),
            )
            .outerjoin(
                ShareObjectItem,
                and_(
                    ShareObjectItem.shareUri == share.shareUri,
                    DatasetStorageLocation.locationUri == ShareObjectItem.itemUri,
                ),
            )
            .filter(DatasetStorageLocation.datasetUri == share.datasetUri)
        )
        if states:
            locations = locations.filter(ShareObjectItem.status.in_(states))

        s3_buckets = (
            session.query(
                DatasetBucket.bucketUri.label('itemUri'),
                func.coalesce('S3Bucket').label('itemType'),
                DatasetBucket.S3BucketName.label('itemName'),
                DatasetBucket.description.label('description'),
                ShareObjectItem.shareItemUri.label('shareItemUri'),
                ShareObjectItem.status.label('status'),
                ShareObjectItem.healthStatus.label('healthStatus'),
                ShareObjectItem.healthMessage.label('healthMessage'),
                ShareObjectItem.lastVerificationTime.label('lastVerificationTime'),
                case(
                    [(ShareObjectItem.shareItemUri.isnot(None), True)],
                    else_=False,
                ).label('isShared'),
            )
            .outerjoin(
                ShareObjectItem,
                and_(
                    ShareObjectItem.shareUri == share.shareUri,
                    DatasetBucket.bucketUri == ShareObjectItem.itemUri,
                ),
            )
            .filter(DatasetBucket.datasetUri == share.datasetUri)
        )
        if states:
            s3_buckets = s3_buckets.filter(ShareObjectItem.status.in_(states))

        shareable_objects = tables.union(locations, s3_buckets).subquery('shareable_objects')
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
            if 'isShared' in data:
                is_shared = data.get('isShared')
                query = query.filter(shareable_objects.c.isShared == is_shared)

            if 'isHealthy' in data:
                # healthy_status = ShareItemHealthStatus.Healthy.value
                query = (
                    query.filter(shareable_objects.c.healthStatus == ShareItemHealthStatus.Healthy.value)
                    if data.get('isHealthy')
                    else query.filter(shareable_objects.c.healthStatus != ShareItemHealthStatus.Healthy.value)
                )

        return paginate(query, data.get('page', 1), data.get('pageSize', 10)).to_dict()

    @staticmethod
    def list_user_received_share_requests(session, username, groups, data=None):
        query = (
            session.query(ShareObject)
            .join(
                Dataset,
                Dataset.datasetUri == ShareObject.datasetUri,
            )
            .filter(
                or_(
                    Dataset.businessOwnerEmail == username,
                    Dataset.businessOwnerDelegationEmails.contains(f'{{{username}}}'),
                    Dataset.stewards.in_(groups),
                    Dataset.SamlAdminGroupName.in_(groups),
                )
            )
        )

        if data and data.get('status'):
            if len(data.get('status')) > 0:
                query = query.filter(ShareObject.status.in_(data.get('status')))
        if data and data.get('dataset_owners'):
            if len(data.get('dataset_owners')) > 0:
                query = query.filter(Dataset.SamlAdminGroupName.in_(data.get('dataset_owners')))
        if data and data.get('datasets_uris'):
            if len(data.get('datasets_uris')) > 0:
                query = query.filter(ShareObject.datasetUri.in_(data.get('datasets_uris')))
        if data and data.get('share_requesters'):
            if len(data.get('share_requesters')) > 0:
                query = query.filter(ShareObject.groupUri.in_(data.get('share_requesters')))
        if data and data.get('share_iam_roles'):
            if len(data.get('share_iam_roles')) > 0:
                query = query.filter(ShareObject.principalIAMRoleName.in_(data.get('share_iam_roles')))
        return paginate(query, data.get('page', 1), data.get('pageSize', 10)).to_dict()

    @staticmethod
    def list_user_sent_share_requests(session, username, groups, data=None):
        query = (
            session.query(ShareObject)
            .join(
                Environment,
                Environment.environmentUri == ShareObject.environmentUri,
            )
            .join(
                Dataset,
                Dataset.datasetUri == ShareObject.datasetUri,
            )
            .filter(
                or_(
                    ShareObject.owner == username,
                    and_(
                        ShareObject.groupUri.in_(groups),
                        ShareObject.principalType.in_([PrincipalType.Group.value, PrincipalType.ConsumptionRole.value]),
                    ),
                )
            )
        )
        if data and data.get('status'):
            if len(data.get('status')) > 0:
                query = query.filter(ShareObject.status.in_(data.get('status')))
        if data and data.get('dataset_owners'):
            if len(data.get('dataset_owners')) > 0:
                query = query.filter(Dataset.SamlAdminGroupName.in_(data.get('dataset_owners')))
        if data and data.get('datasets_uris'):
            if len(data.get('datasets_uris')) > 0:
                query = query.filter(ShareObject.datasetUri.in_(data.get('datasets_uris')))
        if data and data.get('share_requesters'):
            if len(data.get('share_requesters')) > 0:
                query = query.filter(ShareObject.groupUri.in_(data.get('share_requesters')))
        if data and data.get('share_iam_roles'):
            if len(data.get('share_iam_roles')) > 0:
                query = query.filter(ShareObject.principalIAMRoleName.in_(data.get('share_iam_roles')))
        return paginate(query, data.get('page', 1), data.get('pageSize', 10)).to_dict()

    @staticmethod
    def get_share_by_dataset_and_environment(session, dataset_uri, environment_uri):
        environment_groups = session.query(EnvironmentGroup).filter(EnvironmentGroup.environmentUri == environment_uri)
        groups = [g.groupUri for g in environment_groups]
        share = session.query(ShareObject).filter(
            and_(
                ShareObject.datasetUri == dataset_uri,
                ShareObject.environmentUri == environment_uri,
                ShareObject.groupUri.in_(groups),
            )
        )
        if not share:
            raise exceptions.ObjectNotFound('Share', f'{dataset_uri}/{environment_uri}')
        return share

    @staticmethod
    def update_share_object_status(session, share_uri: str, status: str) -> ShareObject:
        share = ShareObjectRepository.get_share_by_uri(session, share_uri)
        share.status = status
        session.commit()
        return share

    @staticmethod
    def update_share_item_status(
        session,
        uri: str,
        status: str,
    ) -> ShareObjectItem:
        share_item = ShareObjectRepository.get_share_item_by_uri(session, uri)
        share_item.status = status
        session.commit()
        return share_item

    @staticmethod
    def update_share_item_health_status(
        session,
        share_item: ShareObjectItem,
        healthStatus: str = None,
        healthMessage: str = None,
        timestamp: datetime = None,
    ) -> ShareObjectItem:
        share_item.healthStatus = healthStatus
        share_item.healthMessage = healthMessage
        share_item.lastVerificationTime = timestamp
        session.commit()
        return share_item

    @staticmethod
    def delete_share_item_status_batch(
        session,
        share_uri: str,
        status: str,
    ):
        (
            session.query(ShareObjectItem)
            .filter(and_(ShareObjectItem.shareUri == share_uri, ShareObjectItem.status == status))
            .delete()
        )

    @staticmethod
    def update_share_item_health_status_batch(
        session,
        share_uri: str,
        old_status: str,
        new_status: str,
    ) -> bool:
        (
            session.query(ShareObjectItem)
            .filter(and_(ShareObjectItem.shareUri == share_uri, ShareObjectItem.healthStatus == old_status))
            .update(
                {
                    ShareObjectItem.healthStatus: new_status,
                }
            )
        )
        return True

    @staticmethod
    def update_share_item_status_batch(
        session,
        share_uri: str,
        old_status: str,
        new_status: str,
    ) -> bool:
        (
            session.query(ShareObjectItem)
            .filter(and_(ShareObjectItem.shareUri == share_uri, ShareObjectItem.status == old_status))
            .update(
                {
                    ShareObjectItem.status: new_status,
                }
            )
        )
        return True

    @staticmethod
    def get_share_data(session, share_uri):
        share: ShareObject = ShareObjectRepository.get_share_by_uri(session, share_uri)

        dataset: Dataset = DatasetRepository.get_dataset_by_uri(session, share.datasetUri)

        source_environment: Environment = session.query(Environment).get(dataset.environmentUri)
        if not source_environment:
            raise exceptions.ObjectNotFound('SourceEnvironment', dataset.environmentUri)

        target_environment: Environment = session.query(Environment).get(share.environmentUri)
        if not target_environment:
            raise exceptions.ObjectNotFound('TargetEnvironment', share.environmentUri)

        env_group: EnvironmentGroup = (
            session.query(EnvironmentGroup)
            .filter(
                and_(
                    EnvironmentGroup.environmentUri == share.environmentUri,
                    EnvironmentGroup.groupUri == share.groupUri,
                )
            )
            .first()
        )
        if not env_group:
            raise Exception(
                f'Share object Team {share.groupUri} is not a member of the '
                f'environment {target_environment.name}/{target_environment.AwsAccountId}'
            )

        source_env_group: EnvironmentGroup = (
            session.query(EnvironmentGroup)
            .filter(
                and_(
                    EnvironmentGroup.environmentUri == dataset.environmentUri,
                    EnvironmentGroup.groupUri == dataset.SamlAdminGroupName,
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
    def get_all_shareable_items(session, share_uri, status=None, healthStatus=None):
        (tables, folders, buckets) = ShareObjectRepository.get_share_data_items(
            session, share_uri, status, healthStatus
        )
        uris = []
        uris.extend([table.tableUri for table in tables])
        uris.extend([folder.locationUri for folder in folders])
        uris.extend([bucket.bucketUri for bucket in buckets])
        return (
            session.query(ShareObjectItem)
            .filter(
                and_(
                    ShareObjectItem.itemUri.in_(uris),
                    ShareObjectItem.shareUri == share_uri,
                )
            )
            .all()
        )

    @staticmethod
    def get_share_data_items(session, share_uri, status=None, healthStatus=None):
        share: ShareObject = ShareObjectRepository.get_share_by_uri(session, share_uri)

        tables = ShareObjectRepository._find_all_share_item(
            session, share, status, healthStatus, DatasetTable, DatasetTable.tableUri
        )

        folders = ShareObjectRepository._find_all_share_item(
            session, share, status, healthStatus, DatasetStorageLocation, DatasetStorageLocation.locationUri
        )

        s3_buckets = ShareObjectRepository._find_all_share_item(
            session, share, status, healthStatus, DatasetBucket, DatasetBucket.bucketUri
        )

        return (
            tables,
            folders,
            s3_buckets,
        )

    @staticmethod
    def _find_all_share_item(session, share, status, healthStatus, share_type_model, share_type_uri):
        query = (
            session.query(share_type_model)
            .join(
                ShareObjectItem,
                ShareObjectItem.itemUri == share_type_uri,
            )
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    ShareObject.datasetUri == share.datasetUri,
                    ShareObject.environmentUri == share.environmentUri,
                    ShareObject.shareUri == share.shareUri,
                )
            )
        )
        if status:
            query = query.filter(ShareObjectItem.status == status)
        if healthStatus:
            query = query.filter(ShareObjectItem.healthStatus == healthStatus)
        return query.all()

    @staticmethod
    def find_all_share_items(session, share_uri, share_type, status=None):
        query = session.query(ShareObjectItem).filter(
            (and_(ShareObjectItem.shareUri == share_uri, ShareObjectItem.itemType == share_type))
        )
        if status:
            query = query.filter(ShareObjectItem.status.in_(status))
        return query.all()

    @staticmethod
    def other_approved_share_item_table_exists(session, environment_uri, item_uri, share_item_uri):
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        return (
            session.query(ShareObject)
            .join(
                ShareObjectItem,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    ShareObject.environmentUri == environment_uri,
                    ShareObjectItem.itemUri == item_uri,
                    ShareObjectItem.shareItemUri != share_item_uri,
                    ShareObjectItem.status.in_(share_item_shared_states),
                )
            )
            .first()
        )

    @staticmethod
    def get_share_items_states(session, share_uri, item_uris=None):
        query = (
            session.query(ShareObjectItem)
            .join(
                ShareObject,
                ShareObjectItem.shareUri == ShareObject.shareUri,
            )
            .filter(
                and_(
                    ShareObject.shareUri == share_uri,
                )
            )
        )
        if item_uris:
            query = query.filter(ShareObjectItem.shareItemUri.in_(item_uris))
        return [item.status for item in query.distinct(ShareObjectItem.status)]

    @staticmethod
    def has_shared_items(session, item_uri: str) -> int:
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        return (
            session.query(ShareObjectItem)
            .filter(and_(ShareObjectItem.itemUri == item_uri, ShareObjectItem.status.in_(share_item_shared_states)))
            .count()
        )

    @staticmethod
    def delete_shares(session, item_uri: str):
        session.query(ShareObjectItem).filter(ShareObjectItem.itemUri == item_uri).delete()

    @staticmethod
    def delete_shares_with_no_shared_items(session, dataset_uri):
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        shares = (
            session.query(ShareObject)
            .outerjoin(ShareObjectItem, ShareObjectItem.shareUri == ShareObject.shareUri)
            .filter(
                and_(
                    ShareObject.datasetUri == dataset_uri,
                    ShareObjectItem.status.notin_(share_item_shared_states),
                )
            )
            .all()
        )
        for share in shares:
            share_items = session.query(ShareObjectItem).filter(ShareObjectItem.shareUri == share.shareUri).all()
            for item in share_items:
                session.delete(item)

            share_obj = session.query(ShareObject).filter(ShareObject.shareUri == share.shareUri).first()
            session.delete(share_obj)

    @staticmethod
    def query_user_shared_datasets(session, username, groups) -> Query:
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        query = (
            session.query(Dataset)
            .outerjoin(
                ShareObject,
                ShareObject.datasetUri == Dataset.datasetUri,
            )
            .outerjoin(ShareObjectItem, ShareObjectItem.shareUri == ShareObject.shareUri)
            .filter(
                or_(
                    and_(
                        ShareObject.principalId.in_(groups),
                        ShareObjectItem.status.in_(share_item_shared_states),
                    ),
                    and_(
                        ShareObject.owner == username,
                        ShareObjectItem.status.in_(share_item_shared_states),
                    ),
                )
            )
        )
        return query.distinct(Dataset.datasetUri)

    @staticmethod
    def find_dataset_shares(session, dataset_uri):
        return session.query(ShareObject).filter(ShareObject.datasetUri == dataset_uri).all()

    @staticmethod
    def query_dataset_shares(session, dataset_uri) -> Query:
        return session.query(ShareObject).filter(
            and_(
                ShareObject.datasetUri == dataset_uri,
                ShareObject.deleted.is_(None),
            )
        )

    @staticmethod
    def paginated_dataset_shares(session, uri, data=None) -> [ShareObject]:
        query = ShareObjectRepository.query_dataset_shares(session, uri)
        return paginate(query=query, page=data.get('page', 1), page_size=data.get('pageSize', 5)).to_dict()

    @staticmethod
    def list_dataset_shares_with_existing_shared_items(
        session, dataset_uri, environment_uri=None, item_type=None
    ) -> [ShareObject]:
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        query = (
            session.query(ShareObject)
            .outerjoin(ShareObjectItem, ShareObjectItem.shareUri == ShareObject.shareUri)
            .filter(
                and_(
                    ShareObject.datasetUri == dataset_uri,
                    ShareObject.deleted.is_(None),
                    ShareObjectItem.status.in_(share_item_shared_states),
                )
            )
        )
        if environment_uri:
            query = query.filter(ShareObject.environmentUri == environment_uri)
        if item_type:
            query = query.filter(ShareObjectItem.itemType == item_type)
        return query.all()

    @staticmethod
    def list_dataset_shares_and_datasets_with_existing_shared_items(
        session, dataset_uri, environment_uri=None, item_type=None
    ) -> [ShareObject]:
        warn(
            'ShareObjectRepository.list_dataset_shares_and_datasets_with_existing_shared_items will be deprecated in v2.6.0',
            DeprecationWarning,
            stacklevel=2,
        )
        # When deprecated, use ist_dataset_shares_with_existing_shared_items instead
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        query = (
            session.query(ShareObject)
            .outerjoin(ShareObjectItem, ShareObjectItem.shareUri == ShareObject.shareUri)
            .filter(
                and_(
                    ShareObject.datasetUri == dataset_uri,
                    ShareObject.deleted.is_(None),
                    ShareObjectItem.status.in_(share_item_shared_states),
                )
            )
        )
        if environment_uri:
            query = query.filter(ShareObject.environmentUri == environment_uri)
        if item_type:
            query = query.filter(ShareObjectItem.itemType == item_type)
        shares_datasets = []
        for share in query.all():
            dataset = DatasetRepository.get_dataset_by_uri(session, share.datasetUri)
            shares_datasets.append(
                {'shareUri': share.shareUri, 'databaseName': f'{dataset.GlueDatabaseName}_shared_{share.shareUri}'}
            )
        return shares_datasets

    @staticmethod
    def delete_all_share_items(session, env_uri):
        env_shared_with_objects = session.query(ShareObject).filter(ShareObject.environmentUri == env_uri).all()
        for share in env_shared_with_objects:
            (session.query(ShareObjectItem).filter(ShareObjectItem.shareUri == share.shareUri).delete())
            session.delete(share)

    @staticmethod
    def paginate_shared_datasets(session, env_uri, data):
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        q = (
            session.query(
                ShareObjectItem.shareUri.label('shareUri'),
                Dataset.datasetUri.label('datasetUri'),
                Dataset.name.label('datasetName'),
                Dataset.description.label('datasetDescription'),
                Environment.environmentUri.label('environmentUri'),
                Environment.name.label('environmentName'),
                ShareObject.created.label('created'),
                ShareObject.principalId.label('principalId'),
                ShareObject.principalType.label('principalType'),
                ShareObject.environmentUri.label('targetEnvironmentUri'),
                ShareObjectItem.itemType.label('itemType'),
                ShareObjectItem.GlueDatabaseName.label('GlueDatabaseName'),
                ShareObjectItem.GlueTableName.label('GlueTableName'),
                ShareObjectItem.S3AccessPointName.label('S3AccessPointName'),
                Organization.organizationUri.label('organizationUri'),
                Organization.name.label('organizationName'),
                case(
                    [
                        (
                            ShareObjectItem.itemType == ShareableType.Table.value,
                            func.concat(
                                DatasetTable.GlueDatabaseName,
                                '.',
                                DatasetTable.GlueTableName,
                            ),
                        ),
                        (
                            ShareObjectItem.itemType == ShareableType.StorageLocation.value,
                            func.concat(DatasetStorageLocation.name),
                        ),
                    ],
                    else_='XXX XXXX',
                ).label('itemAccess'),
            )
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .join(
                Dataset,
                ShareObject.datasetUri == Dataset.datasetUri,
            )
            .join(
                Environment,
                Environment.environmentUri == Dataset.environmentUri,
            )
            .join(
                Organization,
                Organization.organizationUri == Environment.organizationUri,
            )
            .outerjoin(
                DatasetTable,
                ShareObjectItem.itemUri == DatasetTable.tableUri,
            )
            .outerjoin(
                DatasetStorageLocation,
                ShareObjectItem.itemUri == DatasetStorageLocation.locationUri,
            )
            .filter(
                and_(
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObject.environmentUri == env_uri,
                )
            )
        )

        if data.get('datasetUri'):
            dataset_uri = data.get('datasetUri')
            q = q.filter(ShareObject.datasetUri == dataset_uri)

        if data.get('itemTypes', None):
            item_types = data.get('itemTypes')
            q = q.filter(or_(*[ShareObjectItem.itemType == t for t in item_types]))

        if data.get('uniqueShares', False):
            q = q.filter(ShareObject.principalType != PrincipalType.ConsumptionRole.value)
            q = q.distinct(ShareObject.shareUri)

        if data.get('term'):
            term = data.get('term')
            q = q.filter(ShareObjectItem.itemName.ilike('%' + term + '%'))

        return paginate(query=q, page=data.get('page', 1), page_size=data.get('pageSize', 10)).to_dict()

    @staticmethod
    def find_share_items_by_item_uri(session, item_uri):
        return session.query(ShareObjectItem).filter(ShareObjectItem.itemUri == item_uri).all()

    @staticmethod
    def get_approved_share_object(session, item):
        share_object: ShareObject = (
            session.query(ShareObject)
            .filter(
                and_(
                    ShareObject.shareUri == item.shareUri,
                    ShareObject.status == ShareObjectStatus.Approved.value,
                )
            )
            .first()
        )
        return share_object

    @staticmethod
    def get_shared_tables(session, dataset) -> List[ShareObjectItem]:
        return (
            session.query(
                DatasetTable.GlueDatabaseName.label('GlueDatabaseName'),
                DatasetTable.GlueTableName.label('GlueTableName'),
                DatasetTable.S3Prefix.label('S3Prefix'),
                DatasetTable.AWSAccountId.label('SourceAwsAccountId'),
                DatasetTable.region.label('SourceRegion'),
                Environment.AwsAccountId.label('TargetAwsAccountId'),
                Environment.region.label('TargetRegion'),
            )
            .join(
                ShareObjectItem,
                and_(ShareObjectItem.itemUri == DatasetTable.tableUri),
            )
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .join(
                Environment,
                Environment.environmentUri == ShareObject.environmentUri,
            )
            .filter(
                and_(
                    DatasetTable.datasetUri == dataset.datasetUri,
                    DatasetTable.deleted.is_(None),
                    ShareObjectItem.status == ShareObjectStatus.Approved.value,
                )
            )
        ).all()

    @staticmethod
    def get_shared_folders(session, dataset) -> List[DatasetStorageLocation]:
        return (
            session.query(
                DatasetStorageLocation.locationUri.label('locationUri'),
                DatasetStorageLocation.S3BucketName.label('S3BucketName'),
                DatasetStorageLocation.S3Prefix.label('S3Prefix'),
                Environment.AwsAccountId.label('AwsAccountId'),
                Environment.region.label('region'),
            )
            .join(
                ShareObjectItem,
                and_(ShareObjectItem.itemUri == DatasetStorageLocation.locationUri),
            )
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .join(
                Environment,
                Environment.environmentUri == ShareObject.environmentUri,
            )
            .filter(
                and_(
                    DatasetStorageLocation.datasetUri == dataset.datasetUri,
                    DatasetStorageLocation.deleted.is_(None),
                    ShareObjectItem.status == ShareObjectStatus.Approved.value,
                )
            )
        ).all()

    @staticmethod
    def count_principal_shares(session, principal_id: str, environment_uri: str, principal_type: PrincipalType):
        return (
            session.query(ShareObject)
            .filter(
                and_(
                    ShareObject.principalId == principal_id,
                    ShareObject.principalType == principal_type.value,
                    ShareObject.environmentUri == environment_uri,
                )
            )
            .count()
        )

    @staticmethod
    def count_role_principal_shares(session, principal_id: str, principal_type: PrincipalType):
        return (
            session.query(ShareObject)
            .filter(
                and_(
                    ShareObject.principalId == principal_id,
                    ShareObject.principalType == principal_type.value,
                )
            )
            .count()
        )

    @staticmethod
    def query_dataset_tables_shared_with_env(
        session, environment_uri: str, dataset_uri: str, username: str, groups: [str]
    ):
        """For a given dataset, returns the list of Tables shared with the environment
        This means looking at approved ShareObject items
        for the share object associating the dataset and environment
        """
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        env_tables_shared = (
            session.query(DatasetTable)  # all tables
            .join(
                ShareObjectItem,  # found in ShareObjectItem
                ShareObjectItem.itemUri == DatasetTable.tableUri,
            )
            .join(
                ShareObject,  # jump to share object
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    ShareObject.datasetUri == dataset_uri,  # for this dataset
                    ShareObject.environmentUri == environment_uri,  # for this environment
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObject.principalType
                    != PrincipalType.ConsumptionRole.value,  # Exclude Consumption roles shares
                    or_(
                        ShareObject.owner == username,
                        ShareObject.principalId.in_(groups),
                    ),
                )
            )
            .all()
        )

        return env_tables_shared
