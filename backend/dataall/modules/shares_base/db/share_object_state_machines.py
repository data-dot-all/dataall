import logging

from dataall.base.db import exceptions
from dataall.modules.shares_base.services.shares_enums import (
    ShareObjectActions,
    ShareObjectStatus,
    ShareItemActions,
    ShareItemStatus,
)
from dataall.modules.shares_base.db.share_state_machines_repositories import ShareStatusRepository

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
                f'If there is a sharing or revoking in progress wait until it is complete and try again. For share extensions delete unused items and try again',
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
                        ShareObjectStatus.Rejected.value,
                        ShareObjectStatus.Extension_Rejected.value,
                    ]
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
                        ShareObjectStatus.Extension_Rejected.value,
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
                        ShareObjectStatus.Extension_Rejected.value,
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
                        ShareObjectStatus.Extension_Rejected.value,
                    ]
                },
            ),
            ShareObjectActions.Extension.value: Transition(
                name=ShareObjectActions.Extension.value,
                transitions={
                    ShareObjectStatus.Submitted_For_Extension.value: [
                        ShareObjectStatus.Processed.value,
                        ShareObjectStatus.Extension_Rejected.value,
                        ShareObjectStatus.Draft.value,
                    ]
                },
            ),
            ShareObjectActions.ExtensionApprove.value: Transition(
                name=ShareObjectActions.ExtensionApprove.value,
                transitions={ShareObjectStatus.Processed.value: [ShareObjectStatus.Submitted_For_Extension.value]},
            ),
            ShareObjectActions.ExtensionReject.value: Transition(
                name=ShareObjectActions.ExtensionReject.value,
                transitions={
                    ShareObjectStatus.Extension_Rejected.value: [ShareObjectStatus.Submitted_For_Extension.value]
                },
            ),
            ShareObjectActions.CancelExtension.value: Transition(
                name=ShareObjectActions.CancelExtension.value,
                transitions={ShareObjectStatus.Processed.value: [ShareObjectStatus.Submitted_For_Extension.value]},
            ),
        }

    def run_transition(self, transition):
        trans = self.transitionTable[transition]
        new_state = trans.get_transition_target(self._state)
        return new_state

    def update_state(self, session, share, new_state):
        logger.info(f'Updating share object {share.shareUri} in DB from {self._state} to state {new_state}')
        ShareStatusRepository.update_share_object_status(session=session, share_uri=share.shareUri, status=new_state)
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
                    ShareItemStatus.Share_Failed.value: [
                        ShareItemStatus.Share_In_Progress.value,
                        ShareItemStatus.Share_Approved.value,
                    ],
                    ShareItemStatus.Revoke_Failed.value: [
                        ShareItemStatus.Revoke_In_Progress.value,
                        ShareItemStatus.Revoke_Approved.value,
                    ],
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
            ShareObjectActions.Extension.value: Transition(
                name=ShareObjectActions.Extension.value,
                transitions={ShareItemStatus.PendingExtension.value: [ShareItemStatus.Share_Succeeded.value]},
            ),
            ShareObjectActions.ExtensionApprove.value: Transition(
                name=ShareObjectActions.ExtensionApprove.value,
                transitions={ShareItemStatus.Share_Succeeded.value: [ShareItemStatus.PendingExtension.value]},
            ),
            ShareObjectActions.ExtensionReject.value: Transition(
                name=ShareObjectActions.ExtensionReject.value,
                transitions={ShareItemStatus.Share_Succeeded.value: [ShareItemStatus.PendingExtension.value]},
            ),
            ShareObjectActions.CancelExtension.value: Transition(
                name=ShareObjectActions.CancelExtension.value,
                transitions={ShareItemStatus.Share_Succeeded.value: [ShareItemStatus.PendingExtension.value]},
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
                ShareStatusRepository.delete_share_item_status_batch(
                    session=session, share_uri=share_uri, status=self._state
                )
            else:
                logger.info(f'Updating share items in DB from {self._state} to state {new_state}')
                ShareStatusRepository.update_share_item_status_batch(
                    session=session, share_uri=share_uri, old_status=self._state, new_status=new_state
                )
            self._state = new_state
        else:
            logger.info(f'Share Items in DB already in target state {new_state} or no update is required')
            return True

    def update_state_single_item(self, session, share_item, new_state):
        logger.info(f'Updating share item in DB {share_item.shareItemUri} status to {new_state}')
        ShareStatusRepository.update_share_item_status(session=session, uri=share_item.shareItemUri, status=new_state)
        self._state = new_state
        return True
