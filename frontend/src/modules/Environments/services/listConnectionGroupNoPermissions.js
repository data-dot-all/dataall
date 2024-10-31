import { gql } from 'apollo-boost';

export const listConnectionGroupNoPermissions = ({
  filter,
  connectionUri
}) => ({
  variables: {
    connectionUri,
    filter
  },
  query: gql`
    query listConnectionGroupNoPermissions(
      $filter: GroupFilter
      $connectionUri: String!
    ) {
      listConnectionGroupNoPermissions(
        connectionUri: $connectionUri
        filter: $filter
      )
    }
  `
});
