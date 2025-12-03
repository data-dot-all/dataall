import { gql } from 'apollo-boost';

export const markAllNotificationsAsRead = () => ({
  mutation: gql`
    mutation markAllNotificationsAsRead {
      markAllNotificationsAsRead
    }
  `
});
