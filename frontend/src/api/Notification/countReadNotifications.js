import { gql } from 'apollo-boost';

export const countReadNotifications = () => ({
  variables: {},
  query: gql`
    query countReadNotifications {
      countReadNotifications
    }
  `
});
