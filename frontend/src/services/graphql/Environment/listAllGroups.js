import { gql } from 'apollo-boost';

export const listAllGroups = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query listAllGroups($filter: GroupFilter) {
      listAllGroups(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          groupUri
          invitedBy
          created
          description
          environmentIAMRoleArn
          environmentIAMRoleName
          environmentAthenaWorkGroup
        }
      }
    }
  `
});
