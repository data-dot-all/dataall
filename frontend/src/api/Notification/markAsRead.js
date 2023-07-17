import { gql } from 'apollo-boost';

const markNotificationAsRead = (notificationUri) => ({
  variables: {
    notificationUri
  },
  mutation: gql`
    mutation markNotificationAsRead($notificationUri: String!) {
      markNotificationAsRead(notificationUri: $notificationUri)
    }
  `
});

export default markNotificationAsRead;
