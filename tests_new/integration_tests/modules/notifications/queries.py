# TODO: This file will be replaced by using the SDK directly


def mark_notification_read(client, uri):
    query = {
        'operationName': 'markNotificationAsRead',
        'variables': {'notificationUri': uri},
        'query': """
            mutation markNotificationAsRead($notificationUri: String!) {
              markNotificationAsRead(notificationUri: $notificationUri)
            }
                """,
    }
    response = client.query(query=query)
    return response.data.markNotificationAsRead


def list_notifications(client, filter={}):
    query = {
        'operationName': 'listNotifications',
        'variables': {'filter': filter},
        'query': """
            query listNotifications($filter: NotificationFilter) {
              listNotifications(filter: $filter) {
                count
                page
                pages
                hasNext
                hasPrevious
                nodes {
                  notificationUri
                  message
                  type
                  is_read
                  target_uri
                }
              }
            }
                """,
    }
    response = client.query(query=query)
    return response.data.listNotifications


def count_unread_notifications(client):
    query = {
        'operationName': 'countUnreadNotifications',
        'variables': {},
        'query': """
            query countUnreadNotifications {
              countUnreadNotifications
            }
                """,
    }
    response = client.query(query=query)
    return response.data.countUnreadNotifications
