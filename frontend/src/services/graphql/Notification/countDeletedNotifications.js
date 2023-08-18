import { gql } from 'apollo-boost';

export const countDeletedNotifications = () => ({
  variables: {},
  query: gql`
    query countDeletedNotifications {
      countDeletedNotifications
    }
  `
});
