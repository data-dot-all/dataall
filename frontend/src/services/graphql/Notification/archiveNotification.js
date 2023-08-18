import { gql } from 'apollo-boost';

export const archiveNotification = ({ notificationUri }) => ({
  variables: {
    notificationUri
  },
  mutation: gql`
    mutation deleteNotification($notificationUri: String!) {
      deleteNotification(notificationUri: $notificationUri)
    }
  `
});
