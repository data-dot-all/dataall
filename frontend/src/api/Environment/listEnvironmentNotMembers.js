import { gql } from 'apollo-boost';

const listEnvironmentNotMembers = ({ term, environmentUri }) => ({
  variables: {
    environmentUri,
    filter: { term: term || '' }
  },
  query: gql`
    query getEnvironment(
      $filter: OrganizationUserFilter
      $environmentUri: String
    ) {
      getEnvironment(environmentUri: $environmentUri) {
        environmentUri
        userRoleInEnvironment
        notMembers(filter: $filter) {
          count
          nodes {
            userName
            userRoleInEnvironment
            created
          }
        }
      }
    }
  `
});

export default listEnvironmentNotMembers;
