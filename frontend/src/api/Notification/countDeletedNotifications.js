import { gql } from 'apollo-boost';

const countDeletedNotifications = () => ({
  variables: {},
  query: gql`
    query countDeletedNotifications {
      countDeletedNotifications
    }
  `
});

export default countDeletedNotifications;
