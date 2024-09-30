import { gql } from 'apollo-boost';

export const listEnvironmentRedshiftConnections = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query listEnvironmentRedshiftConnections($filter: ConnectionFilter) {
      listEnvironmentRedshiftConnections(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          name
          connectionUri
          SamlGroupName
          redshiftType
          clusterId
          nameSpaceId
          workgroup
          database
          redshiftUser
          secretArn
          connectionType
        }
      }
    }
  `
});
