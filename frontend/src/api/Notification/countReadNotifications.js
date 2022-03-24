import { gql } from 'apollo-boost';

const countReadNotifications = () => ({
  variables: {},
  query: gql`
            query countReadNotifications{
                countReadNotifications
            }
        `
});

export default countReadNotifications;
