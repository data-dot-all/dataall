import { gql } from 'apollo-boost';

export const markNotificationAsRead = (notificationUri) => ({
  variables: {
    notificationUri
  },
  mutation: gql`
    mutation markNotificationAsRead($notificationUri: String!) {
      markNotificationAsRead(notificationUri: $notificationUri)
    }
  `
});
