import { gql } from 'apollo-boost';

const countUnreadNotifications = () => ({
  variables: {},
  query: gql`
            query countUnreadNotifications{
                countUnreadNotifications
            }
        `
});

export default countUnreadNotifications;
