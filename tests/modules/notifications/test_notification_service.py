import os
from unittest import mock
from unittest.mock import MagicMock

import pytest

from dataall.modules.notifications.handlers.notifications_handler import NotificationHandler
from dataall.core.tasks.db.task_models import Task


def mock_cognito_client(mocker):
    mock_client = MagicMock()
    mocker.patch('dataall.modules.notifications.services.ses_email_notification_service.Cognito', mock_client)
    return mock_client


def mock_ses_client_(mocker):
    mock_ses_client = MagicMock()
    mocker.patch(
        'dataall.modules.notifications.services.ses_email_notification_service.Ses.get_ses_client', mock_ses_client
    )
    return mock_ses_client


# Test notification's service for email notification type
def test_notification_service_email(mocker, db):
    # Mock SES Client
    mock_ses_client = mock_ses_client_(mocker)
    mock_ses_client().send_email.return_value = True

    # Mock Cognito Client
    cognito_client = mock_cognito_client(mocker)
    cognito_client().get_user_emailids_from_group.return_value = ['bob@email.com', 'bob-1@email.com']

    # Mock the ServiceProviderFactory Call
    mocker.patch(
        'dataall.modules.notifications.services.ses_email_notification_service.ServiceProviderFactory.get_service_provider_instance',
        return_value=cognito_client(),
    )

    # Create an email task
    with db.scoped_session() as session:
        notification_task: Task = Task(
            action='notification.service',
            targetUri='some_share_uri',
            payload={
                'notificationType': 'email',
                'subject': 'subject',
                'message': 'message',
                'recipientGroupsList': ['requesterGroupName', 'datasetOwnerGroup', 'datasetStewardsGroup'],
                'recipientEmailList': ['email@email.com'],
            },
        )
        session.add(notification_task)
        session.commit()

        NotificationHandler.notification_service(db, notification_task)

    cognito_client().get_user_emailids_from_group.assert_called()
    cognito_calls = cognito_client().get_user_emailids_from_group.call_args_list
    group_name_list_used_for_share = [x.args[0] for x in cognito_calls]
    assert (
        'datasetOwnerGroup' in group_name_list_used_for_share
        and 'datasetStewardsGroup' in group_name_list_used_for_share
        and 'requesterGroupName' in group_name_list_used_for_share
    )
    mock_ses_client().send_email.assert_called()
    # Check if the email send method is called three times for ["bob@email.com", "bob-1@email.com", "email@email.com"]
    assert mock_ses_client().send_email.call_count == 3


# Test to check when unknown notification type is used
# Added function to check the if-else logic in notification handler
def test_notification_service_when_incorrect_task_is_created(mocker, db):
    # Mock the email notification provider.send_email_task
    email_notification_service = mocker.patch(
        'dataall.modules.notifications.services.ses_email_notification_service.SESEmailNotificationService.send_email_task',
        return_value=None,
    )

    with db.scoped_session() as session:
        notification_task: Task = Task(
            action='notification.service',
            targetUri='some_share_uri',
            payload={
                'notificationType': 'WrongService',
                'subject': 'subject',
                'message': 'message',
                'recipientGroupsList': ['requesterGroupName', 'datasetOwnerGroup', 'datasetStewardsGroup'],
                'recipientEmailList': [],
            },
        )
        session.add(notification_task)
        session.commit()

        NotificationHandler.notification_service(db, notification_task)

    email_notification_service.assert_not_called()


# Test to check when empty email id set is returned by cognito
def test_notification_service_with_no_email_ids_in_group(mocker, db):
    # Mock SES Client
    mock_ses_client = mock_ses_client_(mocker)
    mock_ses_client().send_email.return_value = True

    # Mock Cognito Client
    cognito_client = mock_cognito_client(mocker)
    cognito_client().get_user_emailids_from_group.return_value = []

    # Mock the ServiceProviderFactory Call
    mocker.patch(
        'dataall.modules.notifications.services.ses_email_notification_service.ServiceProviderFactory.get_service_provider_instance',
        return_value=cognito_client(),
    )

    with db.scoped_session() as session:
        notification_task: Task = Task(
            action='notification.service',
            targetUri='some_share_uri',
            payload={
                'notificationType': 'email',
                'subject': 'subject',
                'message': 'message',
                'recipientGroupsList': ['requesterGroupName', 'datasetOwnerGroup', 'datasetStewardsGroup'],
                'recipientEmailList': [],
            },
        )
        session.add(notification_task)
        session.commit()

        NotificationHandler.notification_service(db, notification_task)

    # Check that the send email was not called
    assert mock_ses_client().send_email.call_count == 0


# Test to check when sender email id is None. This can happen when the custom_domain is present/absent and the config for email is set to true in config.json
@mock.patch.dict(os.environ, {'email_sender_id': 'none'})
def test_notification_service_with_sender_email_id_is_none(mocker, db):
    # Mock Cognito Client
    cognito_client = mock_cognito_client(mocker)
    cognito_client().get_user_emailids_from_group.return_value = ['bob@email.com']

    # Mock the ServiceProviderFactory Call
    mocker.patch(
        'dataall.modules.notifications.services.ses_email_notification_service.ServiceProviderFactory.get_service_provider_instance',
        return_value=cognito_client(),
    )

    with db.scoped_session() as session:
        notification_task: Task = Task(
            action='notification.service',
            targetUri='some_share_uri',
            payload={
                'notificationType': 'email',
                'subject': 'subject',
                'message': 'message',
                'recipientGroupsList': ['requesterGroupName', 'datasetOwnerGroup', 'datasetStewardsGroup'],
                'recipientEmailList': [],
            },
        )
        session.add(notification_task)
        session.commit()

        # Check if the ses initialization module raises an exception when the email id is not present
        with pytest.raises(Exception) as exception:
            NotificationHandler.notification_service(db, notification_task)
        assert str(exception.value) == 'email_sender_id environment variable is not set'
