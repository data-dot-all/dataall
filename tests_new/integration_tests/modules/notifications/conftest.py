# import pytest
# from integration_tests.core.vpc.queries import create_network, delete_network


# @pytest.fixture(scope='function')
# def notification1(client1):
#     notification = None
#     try:
#         notification = create_notification(...)
#         yield notification
#     finally:
#         if notification:
#             delete_notification(client1, uri==notification.notificationUri)
