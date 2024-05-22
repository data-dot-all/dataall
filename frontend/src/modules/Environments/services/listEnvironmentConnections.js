import { gql } from 'apollo-boost';

export const listEnvironmentConnections = ({ filter, environmentUri }) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
    query listEnvironmentConnections(
      $filter: ConnectionsFilter
      $environmentUri: String!
    ) {
      listEnvironmentConnections(
        environmentUri: $environmentUri
        filter: $filter
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          connectionUri
          connectionName
          connectionType
          SamlGroupName
        }
      }
    }
  `
});
