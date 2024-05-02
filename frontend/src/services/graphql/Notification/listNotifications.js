import { gql } from 'apollo-boost';

export const listNotifications = (filter) => ({
  variables: {
    filter
  },
  query: gql`
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
  `
});
