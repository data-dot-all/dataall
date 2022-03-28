import { gql } from 'apollo-boost';

const listEnvironmentNotInvitedGroups = ({ filter, environmentUri }) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
    query listEnvironmentNotInvitedGroups(
      $filter: GroupFilter
      $environmentUri: String
    ) {
      listEnvironmentNotInvitedGroups(
        environmentUri: $environmentUri
        filter: $filter
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          groupUri
        }
      }
    }
  `
});

export default listEnvironmentNotInvitedGroups;
