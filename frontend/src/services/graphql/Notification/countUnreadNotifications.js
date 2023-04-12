import { gql } from 'apollo-boost';

export const countUnreadNotifications = () => ({
  variables: {},
  query: gql`
    query countUnreadNotifications {
      countUnreadNotifications
    }
  `
});
