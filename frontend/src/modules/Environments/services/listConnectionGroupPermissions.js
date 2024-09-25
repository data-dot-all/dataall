import { gql } from 'apollo-boost';

export const listConnectionGroupPermissions = ({ filter, connectionUri }) => ({
  variables: {
    connectionUri,
    filter
  },
  query: gql`
    query listConnectionGroupPermissions(
      $filter: GroupFilter
      $connectionUri: String!
    ) {
      listConnectionGroupPermissions(
        connectionUri: $connectionUri
        filter: $filter
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          groupUri
          permissions {
            name
            description
          }
        }
      }
    }
  `
});
