import { gql } from 'apollo-boost';

export const listEnvironmentConnections = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query listEnvironmentConnections($filter: ConnectionFilter) {
      listEnvironmentConnections(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          name
          connectionUri
          connectionName
          connectionType
          SamlGroupName
        }
      }
    }
  `
});
